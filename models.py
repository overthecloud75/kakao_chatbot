import datetime
import copy
from views.config import page_default
from utils import calculate_accuracy, paginate
from werkzeug.security import check_password_hash
from pymongo import MongoClient

mongoClient = MongoClient('mongodb://localhost:27017/')
db = mongoClient['chatbot']

# users
def post_sign_up(request_data):
    collection = db['users']
    user_data = collection.find_one(filter={'email': request_data['email']})
    error = None
    if user_data:
        error = '이미 존재하는 사용자입니다.'
    else:
        user_data = collection.find_one(sort=[('create_time', -1)])
        if user_data:
            user_id = user_data['user_id'] + 1
        else:
            user_id = 1
        request_data['create_time'] = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        request_data['user_id'] = user_id
        collection.insert(request_data)
    return error

def post_login(request_data):
    collection = db['users']
    error = None
    user_data = collection.find_one(filter={'email': request_data['email']})
    if not user_data:
        error = "존재하지 않는 사용자입니다."
    elif not check_password_hash(user_data['password'], request_data['password']):
        error = "비밀번호가 올바르지 않습니다."
    return error, user_data

# bayesianFilter.py
def set_baysien():
    collection = db['bayesian']

    words = []
    data_list = collection.find({'type':'words'})
    for data in data_list:
        words.append(data['word'])
    data = collection.find_one(filter={'word_dict': {'$exists': 'true'}})
    word_dict = data['word_dict']

    category_dict = {}
    data_list = collection.find({'type':'intent'})
    for data in data_list:
        category_dict[data['intent']] = data['count']

    word_count = {}
    data_list = collection.find({'type':'word_count'})
    for data in data_list:
        word_count[data['word']] = data['count']
    return words, word_dict, category_dict, word_count

# api_views.py
def set_deep():
    collection = db['deep']

    word_index = {}
    data_list = collection.find({'type':'word_index'})
    for data in data_list:
        word_index[data['word']] = data['idx']
    idx_label = {}
    data_list = collection.find({'type':'idx_label'})
    for data in data_list:
        idx_label[data['idx']] = data['label']

    data = collection.find_one(filter={'max_len_list':{'$exists':'true'}})
    max_len = data['max_len_list'][0]
    return word_index, idx_label, max_len

def kakaoWrite(msg, spacetext, corpus, words, deepScore, bayScore):
    data = {'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
               'msg': msg,
               'spacetext': spacetext,
               'corpus': corpus,
               'words': words,
               'deep': deepScore,
               'bay': bayScore,
               }
    collection = db['kakao']
    collection.insert(data)

# intent_view.py
def get_intent_paging(page=1, sort=None, keyword=None):
    if sort is None or sort == '':
        sort = [('count', -1)]
    per_page = page_default['per_page']
    offset = (page - 1) * per_page
    collection = db['bayesian']
    if keyword is None or keyword == '':
        data_list = collection.find({'type':'intent'}, sort=sort)
    else:
        data_list = collection.find({'type':'intent', 'intent':{'$regex':keyword}}, sort=sort)
    count = data_list.count()
    data_list = data_list.limit(per_page).skip(offset)
    paging = paginate(page, per_page, count)
    return paging, data_list

def get_intent_data_list(intent, page=1, keyword=None):
    per_page = page_default['per_page']
    offset = (page - 1) * per_page
    collection = db['intent']
    if  keyword is None or keyword == '':
        data_list = collection.find({'intent':intent})
    else:
        data_list = collection.find({'intent':intent, 'msg':{'$regex':keyword}})
    count = data_list.count()
    data_list = data_list.limit(per_page).skip(offset)
    paging = paginate(page, per_page, count)
    return paging, data_list

def post_intent(request_data):
    intent = request_data['intent']
    collection = db['bayesian']
    data = collection.find_one({'type':'intent', 'intent':intent})
    if 'msg' in request_data:
        if data:
            collection = db['intent']
            data = collection.find_one(request_data)
            if data is None:
                update = copy.deepcopy(request_data)
                update['timestamp'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                collection.update_one({'intent':intent},{'$set':update}, upsert=True)
                count = collection.find({'intent':intent}).count()
                collection = db['bayesian']
                update = {'count':count}
                collection.update_one({'type':'intent', 'intent':intent}, {'$set':update}, upsert=True)
    else:
        if data is None:
            insert = {'type':'intent', 'intent':intent, 'count':0, 'timestamp':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            collection.insert_one(insert)

#monitoring_view.py
def get_category_list():
    collection = db['bayesian']
    category_list = []
    data_list = collection.find({'type':'intent'})
    for data in data_list:
        category_list.append(data['intent'])
    return category_list

def get_nlp_list(page=1, keyword=None):
    per_page = page_default['per_page']
    offset = (page - 1) * per_page
    collection = db['nlp']
    if keyword is None or keyword == '':
        data_list = collection.find().limit(per_page).skip(offset)
    else:
        data_list = collection.find({'words':{'$regex':keyword}}).limit(per_page).skip(offset)
    count = data_list.count()
    paging = paginate(page, per_page, count)
    return paging, data_list

def get_monitoring_data_list(page=1, sort=None, keyword=None):
    if sort is None or sort == '':
        sort = [('timestamp', -1)]
    per_page = page_default['per_page']
    offset = (page - 1) * per_page
    collection = db['kakao']
    if keyword is None or keyword == '':
        data_list = collection.find(sort=sort).limit(per_page).skip(offset)
    else:
        data_list = collection.find({'msg':{'$regex':keyword}}, sort=sort).limit(per_page).skip(offset)
    count = data_list.count()
    paging = paginate(page, per_page, count)
    return paging, data_list

def post_monitoring(timestamp=None, category=None):
    collection = db['kakao']
    collection.update_one({'timestamp':timestamp}, {'$set':{'category':category}})

def get_statistics_list(page=1, sort=None):
    if sort is None or sort == '':
        sort = [('date', -1)]
    per_page = page_default['per_page']
    offset = (page - 1) * per_page
    today = datetime.date.today()
    # except weekend
    if today.weekday() == 5:
        today = today - datetime.timedelta(days=1)
    elif today.weekday() == 6:
        today = today - datetime.timedelta(days=2)

    days = 1
    while days < 7:  # to prevent a lot of accuracy calculation
        collection = db['kakao']
        str_today = str(today)
        today_find = collection.find({'timestamp':{'$regex':str_today}})
        count = today_find.count()
        if count:
            count, unknown, no_decision, deep_accuracy, bay_accuracy = calculate_accuracy(count, today_find)
            data = {'date':str_today, 'count':count, 'unknown':unknown, 'no_decision':no_decision, 'deep_accuracy':deep_accuracy, 'bay_accuracy':bay_accuracy}
            collection = db['statistics']
            collection.update_one({'date':str_today}, {'$set':data}, upsert=True)
            if no_decision:
                days = 0
        today = today - datetime.timedelta(days=1)
        # except weekend
        if today.weekday() == 5:
            today = today - datetime.timedelta(days=1)
        elif today.weekday() == 6:
            today = today - datetime.timedelta(days=2)
        days = days + 1
    collection = db['statistics']
    count = collection.count()
    data_list = collection.find(sort=sort).limit(per_page).skip(offset)
    paging = paginate(page, per_page, count)
    return paging, data_list

# word_view
def get_word_list(page=1, sort=None, keyword=None):
    if sort is None or sort == '':
        sort = [('count', -1)]
    per_page = page_default['per_page']
    offset = (page - 1) * per_page
    collection = db['bayesian']
    if keyword is None or keyword == '':
        data_list = collection.find({'type':'word_count'}, sort=sort).limit(per_page).skip(offset)
    else:
        data_list = collection.find({'type':'word_count', 'word':{'$regex':keyword}}, sort=sort).limit(per_page).skip(offset)
    count = data_list.count()
    paging = paginate(page, per_page, count)
    return paging, data_list

def get_word_synonym():
    collection = db['preprocess']
    synonym = {}
    data_list = collection.find({'type':'synonym'})
    for data in data_list:
        if data['sub'] in synonym:
            synonym[data['sub']].append(data['word'])
        else:
            synonym[data['sub']] = [data['word']]
    return synonym

def post_pre_word(request_data):
    type = request_data['type']
    word = request_data['word']
    sub = request_data['sub']
    collection = db['preprocess']
    bayesianUpdate = False
    if type == 'synonym' and sub != '':
        collection.update_one({'type':type, 'word':word}, {'$set':{'type':type, 'word':word, 'sub':sub}}, upsert=True)
        bayesianUpdate = True
    elif type == 'stopwords':
        collection.update_one({'type':type, 'word':word}, {'$set':{'type':type, 'word':word}}, upsert=True)
        bayesianUpdate = True
    elif type == 'split' and word in sub:
        collection.update_one({'type':type, 'word':word}, {'$set':{'type':type, 'word':word, 'sub':sub}}, upsert=True)
    elif type == 'custom_vocab' and word in sub:
        collection.update_one({'type':type, 'word':sub}, {'$set':{'type':type, 'word':sub}}, upsert=True)
    # word_count에 있는 word를 삭제하고 sub쪽에 단어를 증가
    if bayesianUpdate:
        collection = db['bayesian']
        word_count = collection.find_one({'type':'word_count', 'word':word})
        count = 0
        if word_count:
            count = word_count['count']
            collection.delete_one({'type':'word_count', 'word':word})

        sub_split = sub.split(' ')
        if len(sub.split(' ')) > 1:
            for sub in sub_split:
                sub_count = collection.find_one({'type':'word_count', 'word':sub})
                if sub_count:
                    count = sub_count['count'] + count
                    collection.update_one({'type':'word_count', 'word':sub}, {'$set':{'count':count}})
        else:
            sub_count = collection.find_one({'type':'word_count', 'word':sub})
            if sub_count:
                count = sub_count['count'] + count
                collection.update_one({'type':'word_count', 'word':sub}, {'$set':{'count':count}})
