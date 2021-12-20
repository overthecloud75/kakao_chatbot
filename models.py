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
    if data is not None:
        word_dict = data['word_dict']
    else:
        word_dict = {}

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
        count = collection.count_documents({'type':'intent'})
    else:
        data_list = collection.find({'type':'intent', 'intent':{'$regex':keyword}}, sort=sort)
        count = collection.count_documents({'type':'intent', 'intent':{'$regex':keyword}})
    data_list = data_list.limit(per_page).skip(offset)
    paging = paginate(page, per_page, count)
    return paging, data_list, count

def get_intent_data_list(intent, page=1, keyword=None):
    per_page = page_default['per_page']
    offset = (page - 1) * per_page
    collection = db['intent']
    if  keyword is None or keyword == '':
        data_list = collection.find({'intent':intent})
        count = collection.count_documents({'intent':intent})
    else:
        data_list = collection.find({'intent':intent, 'msg':{'$regex':keyword}})
        count = collection.count_documents({'intent':intent, 'msg':{'$regex':keyword}})
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
                collection.update_one({'msg':update['msg']},{'$set':update}, upsert=True)
                count = collection.count_documents({'intent':intent})
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
        data_list = collection.find(sort = [('timestamp', -1)]).limit(per_page).skip(offset)
        count = collection.count_documents({}, limit=per_page, skip=offset)
    else:
        data_list = collection.find({'words':{'$regex':keyword}}, sort = [('timestamp', -1)]).limit(per_page).skip(offset)
        count = collection.count_documents({'words':{'$regex':keyword}}, limit=per_page, skip=offset)
    paging = paginate(page, per_page, count)
    return paging, data_list

def get_nlp_wrong_list(page=1, keyword=None):
    per_page = page_default['per_page']
    offset = (page - 1) * per_page
    collection = db['wrong_prediction']
    if keyword is None or keyword == '':
        data_list = collection.find().limit(per_page).skip(offset)
        count = collection.count_documents({}, limit=per_page, skip=offset)
    else:
        data_list = collection.find({'words':{'$regex':keyword}}).limit(per_page).skip(offset)
        count = collection.count_documents({'words':{'$regex':keyword}}, limit=per_page, skip=offset)
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
        count = collection.count_documents({}, limit=per_page, skip=offset)
    else:
        data_list = collection.find({'msg':{'$regex':keyword}}, sort=sort).limit(per_page).skip(offset)
        count = collection.count_documents({'msg':{'$regex':keyword}}, limit=per_page, skip=offset)
        # https://stackoverflow.com/questions/4415514/in-mongodbs-pymongo-how-do-i-do-a-count

    paging = paginate(page, per_page, count)
    return paging, data_list

def post_monitoring(timestamp=None, category=None):
    collection = db['kakao']
    collection.update_one({'timestamp':timestamp}, {'$set':{'category':category}})

def get_accuracy_list(page=1, sort=None):
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
        count = collection.count_documents({'timestamp':{'$regex':str_today}})
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
    count = collection.count_documents({})
    data_list = collection.find(sort=sort).limit(per_page).skip(offset)
    paging = paginate(page, per_page, count)
    return paging, data_list

def get_statistics_list():
    collection = db['statistics']
    accuracy_list = collection.find(sort=[('date', 1)])
    collection = db['bayesian']
    word_list = collection.find({'type':'word_count'}, sort=[('count', -1)])
    return accuracy_list, word_list

# word_view
def get_word_list(page=1, sort=None, keyword=None):
    if sort is None or sort == '':
        sort = [('count', -1)]
    per_page = page_default['per_page']
    offset = (page - 1) * per_page
    collection = db['bayesian']
    if keyword is None or keyword == '':
        data_list = collection.find({'type':'word_count'}, sort=sort).limit(per_page).skip(offset)
        count = collection.count_documents({'type': 'word_count'}, limit=per_page, skip=offset)
    else:
        data_list = collection.find({'type':'word_count', 'word':{'$regex':keyword}}, sort=sort).limit(per_page).skip(offset)
        count = collection.count_documents({'type':'word_count', 'word':{'$regex':keyword}}, limit=per_page, skip=offset)
    paging = paginate(page, per_page, count)
    return paging, data_list

def get_word_typo():
    collection = db['preprocess']
    typo = {}
    data_list = collection.find({'type':'typo'})
    for data in data_list:
        if data['sub'] in typo:
            typo[data['sub']].append(data['word'])
        else:
            typo[data['sub']] = [data['word']]
    return typo

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

def get_typo_synonym():
    typo_synonym = get_word_typo()
    collection = db['preprocess']
    data_list = collection.find({'type': 'synonym'})
    for data in data_list:
        if data['sub'] in typo_synonym:
            typo_synonym[data['sub']].append(data['word'])
        else:
            typo_synonym[data['sub']] = [data['word']]
    return typo_synonym

def post_pre_word(request_data):
    type = request_data['type']
    word = request_data['word']
    sub = request_data['sub']
    collection = db['preprocess']
    bayesianUpdate = False
    if (type == 'synonym' or type == 'typo') and sub != '':
        collection.update_one({'type':type, 'word':word}, {'$set':{'type':type, 'word':word, 'sub':sub}}, upsert=True)
        bayesianUpdate = True
    elif type == 'stopwords':
        collection.update_one({'type':type, 'word':word}, {'$set':{'type':type, 'word':word}}, upsert=True)
        bayesianUpdate = True
    elif type == 'split':
        subSplit = sub.split(' ')
        subWord = ''
        for split in subSplit:
            subWord = subWord + split
        if word == subWord:
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

def get_pre_words(page, sort=None, keyword=None):
    if sort is None or sort == '' or sort == [('count', -1)]:
        sortType = True
    else:
        sortType = False
    if keyword not in ['typo', 'synonym', 'split', 'custom_vocab', 'stopwords']:
        keyword = 'typo'
    per_page = page_default['per_page']
    offset = (page - 1) * per_page

    collection = db['preprocess']
    if (keyword == 'typo' or keyword == 'synonym' or keyword == 'split') and sortType:
        pipeline = [{'$match':{'type':keyword}}, {'$group':{'_id':'$sub', 'count':{'$avg':'$count'}}}, {'$sort':{'count':-1}}]
    elif (keyword == 'typo' or keyword == 'synonym' or keyword == 'split') and not sortType:
        pipeline = [{'$match':{'type':keyword}}, {'$group':{'_id':'$sub', 'count':{'$avg':'$count'}}}, {'$sort':{'count':1}}]
    elif (keyword == 'custom_vocab' or keyword == 'stopwords') and sortType:
        pipeline = [{'$match':{'type':keyword}}, {'$group':{'_id':'$word', 'count':{'$avg':'$count'}}}, {'$sort':{'count':-1}}]
    else:
        pipeline = [{'$match':{'type':keyword}}, {'$group':{'_id':'$word', 'count':{'$avg':'$count'}}}, {'$sort':{'count':1}}]

    data_list = collection.aggregate(pipeline) #.limit(per_page).skip(offset)
    new_data_list = []
    useless_word_count = 0
    for data in data_list:
        count = int(data['count'])
        if count == 0:
            useless_word_count = useless_word_count + 1
        new_data_list.append({'word':data['_id'], 'count':int(data['count'])})
    count = len(new_data_list)
    new_data_list = new_data_list[offset:offset+per_page]
    paging = paginate(page, per_page, count)
    return paging, new_data_list, keyword, useless_word_count

# train
def get_post_nlp(filter=None, preProcessing=None):
    intent_train = []
    label_train = []
    label_idx = {}
    idx_label = {}

    collection = db['intent']
    data_list = collection.find()
    intent_total_count = collection.count_documents({})
    db.drop_collection('nlp')
    collection = db['nlp']
    for data in data_list:
        msg = data['msg']
        intent = data['intent']
        if intent in label_idx:
            idx = label_idx[intent]
            label_train.append(idx)
        else:
            idx_label[str(len(label_idx))] = intent
            label_idx[intent] = len(label_idx)
            idx = label_idx[intent]
            label_train.append(idx)
            # Why using integer as a key with pymongo doesn't work?
            # https://stackoverflow.com/questions/21592468/why-using-integer-as-a-key-with-pymongo-doesnt-work

        spacetext, corpus, words = preProcessing.split(msg)
        filter.fit(words, intent)
        if 'timestamp' in data:
            update = {'timestamp':data['timestamp'], 'msg':msg, 'spacetext':spacetext, 'corpus':corpus,
                      'words':words, 'intent':intent}
        else:
            update = {'msg':msg, 'spacetext':spacetext, 'corpus':corpus, 'words':words, 'intent':intent}

        collection.update_one({'msg':msg}, {'$set':update}, upsert=True)
        intent_train.append(words)
    return intent_total_count, intent_train, label_train, label_idx, idx_label

def post_bayesian(filter=None):
    # How to drop a collection with pymongo?
    # https://stackoverflow.com/questions/48923682/how-to-drop-a-collection-with-pymongo

    collection = db['bayesian']
    data_list = collection.find({'type':'word_count'})
    old_word_count = {}
    for data in data_list:
        old_word_count[data['word']] = data['count']

    db.drop_collection('bayesian')
    collection = db['bayesian']

    for word in list(filter.words):
        update = {'type':'words', 'word':word}
        collection.update_one({'type':'words', 'word':word}, {'$set':update}, upsert=True)
    update = {'word_dict':filter.word_dict}
    collection.update_one({'word_dict':{'$exists':'true'}}, {'$set':update}, upsert=True)
    for key in filter.category_dict:
        update = {'type':'intent', 'intent':key, 'count':filter.category_dict[key]}
        collection.update_one({'type':'intent', 'intent':key}, {'$set':update}, upsert=True)
    word_count = filter.get_total_word_count()
    for key in word_count:
        update = {'type':'word_count', 'word':key, 'count':word_count[key]}
        collection.update_one({'type':'word_count', 'word':key}, {'$set':update}, upsert=True)

    word_difference = []

    for key in old_word_count:
        if key in word_count:
            del word_count[key]
        else:
            word_difference.append((key, -1))

    for key in word_count:
        word_difference.append((key, 1))

    return word_difference

def post_prewordCount(preProcessing=None):
    typo_count = preProcessing.typo_count
    synonym_count = preProcessing.synonym_count
    custom_vocab_count = preProcessing.custom_vocab_count
    stopwords_count = preProcessing.stopwords_count
    split_words_count = preProcessing.split_words_count

    collection = db['preprocess']
    for word in typo_count:
        update = {'type':'typo', 'sub':word, 'count':typo_count[word]}
        collection.update_many({'type':'typo', 'sub':word}, {'$set':update}, upsert=True)

    for word in synonym_count:
        update = {'type':'synonym', 'sub':word, 'count':synonym_count[word]}
        collection.update_many({'type':'synonym', 'sub':word}, {'$set':update}, upsert=True)

    for word in custom_vocab_count:
        update = {'type':'custom_vocab', 'word':word, 'count':custom_vocab_count[word]}
        collection.update_many({'type':'custom_vocab', 'word':word}, {'$set':update}, upsert=True)

    for word in stopwords_count:
        update = {'type':'stopwords', 'word':word, 'count':stopwords_count[word]}
        collection.update_many({'type':'stopwords', 'word':word}, {'$set':update}, upsert=True)

    for word in split_words_count:
        update = {'type':'split', 'sub':word, 'count':split_words_count[word]}
        collection.update_many({'type':'split', 'sub':word}, {'$set':update}, upsert=True)

def post_deepmodel(word_index, idx_label, max_len_list):
    db.drop_collection('deep')
    collection = db['deep']
    for word in word_index:
        update = {'type':'word_index', 'word':word, 'idx':word_index[word]}
        collection.update_one({'type':'word_index', 'word':word}, {'$set':update}, upsert=True)
    for word in idx_label:
        update = {'type':'idx_label', 'idx':word, 'label':idx_label[word]}
        collection.update_one({'type':'idx_label', 'idx':word}, {'$set':update}, upsert=True)
    update = {'max_len_list':max_len_list}
    collection.update_one({'max_len_list':{'$exists':'true'}}, {'$set':update}, upsert=True)

def get_nlp_msg():
    collection = db['nlp']
    data_list = collection.find(sort = [('timestamp', -1)])
    msg_list = []
    for data in data_list:
        msg_list.append((data['msg'], data['intent']))
    return msg_list

def post_nlp_wrong(wrong_nlp_list):
    db.drop_collection('wrong_prediction')
    collection = db['wrong_prediction']
    for update in wrong_nlp_list:
        collection.update_one(update, {'$set':update}, upsert=True)


