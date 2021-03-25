import datetime
from views.config import page_default
from utils import calculate_accuracy, paginate
from pymongo import MongoClient

mongoClient = MongoClient('mongodb://localhost:27017/')
db = mongoClient['chatbot']

# bayesianFilter.py
def set_baysien():
    collection = db['bayesian']

    data = collection.find_one(filter={'words': {'$exists': 'true'}})
    words = data['words']
    data = collection.find_one(filter={'word_dict': {'$exists': 'true'}})
    word_dict = data['word_dict']
    data = collection.find_one(filter={'category_dict': {'$exists': 'true'}})
    category_dict = data['category_dict']
    data = collection.find_one(filter={'word_count': {'$exists': 'true'}})
    word_count = data['word_count']
    return words, word_dict, category_dict, word_count

# api_views.py
def set_deep():
    collection = db['deep']

    data = collection.find_one(filter={'word_index': {'$exists': 'true'}})
    word_index = data['word_index']
    data = collection.find_one(filter={'idx_label': {'$exists': 'true'}})
    idx_label = data['idx_label']
    data = collection.find_one(filter={'max_len_list': {'$exists': 'true'}})
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
def get_intent_list():
    collection = db['bayesian']
    data = collection.find_one(filter={'category_dict': {'$exists': 'true'}})
    category_dict = data['category_dict']

    intent_list = []
    for key in category_dict:
        intent = {'intent':key, 'count':category_dict[key]}
        intent_list.append(intent)
    return intent_list

def get_intent_paging(intent_list, page=1, sort=None):
    per_page = page_default['per_page']
    offset = (page - 1) * per_page
    count = len(intent_list)
    paging = paginate(page, per_page, count)
    data_list = intent_list[offset:offset + per_page]
    return paging, data_list

def get_intent_data_list(intent, page=1):
    per_page = page_default['per_page']
    offset = (page - 1) * per_page
    collection = db['intent']
    data_list = collection.find(
        filter={'intent':intent}
    )
    count = data_list.count()
    data_list = data_list.limit(per_page).skip(offset)
    paging = paginate(page, per_page, count)
    return paging, data_list

def post_intent(request_data):
    if 'msg' in request_data:
        collection = db['intent']
        collection.update_one(request_data, {'$set':request_data}, upsert=True)
    else:
        collection = db['bayesian']
        data = collection.find_one(filter={'category_dict': {'$exists': 'true'}})
        category_dict = data['category_dict']
        intent = request_data['intent']
        if request_data['intent'] in category_dict:
            pass
        else:
            category_dict[intent] = 0
            collection.update_one({'category_dict': {'$exists': 'true'}}, {'$set': {'category_dict' : category_dict}}, upsert=True)

def get_nlp_list(page=1, keyword=None):
    per_page = page_default['per_page']
    offset = (page - 1) * per_page
    collection = db['nlp']
    if keyword:
        data_list = collection.find({'words':{'$regex':keyword}}).limit(per_page).skip(offset)
    else:
        data_list = collection.find().limit(per_page).skip(offset)
    count = data_list.count()
    paging = paginate(page, per_page, count)
    return paging, data_list

def get_word_list(page=1, sort=None):
    if sort is None:
        sort = [('count', -1)]
    per_page = page_default['per_page']
    offset = (page - 1) * per_page
    collection = db['bayesian']
    data = collection.find_one(filter={'word_count': {'$exists': 'true'}}, )
    word_count = data['word_count']
    collection = db['deep']
    data = collection.find_one(filter={'index_word': {'$exists': 'true'}})
    data_list = []
    count = len(data['index_word'])
    index_word = data['index_word']
    if sort[0][1] == 1:
        index_word.reverse()
    index_word = index_word[offset:offset+per_page]
    for word in index_word:
        data_list.append({'word':word, 'count':word_count[word]})
    paging = paginate(page, per_page, count)
    return paging, data_list

#monitoring_view.py
def get_category_list():
    collection = db['bayesian']
    data = collection.find_one(filter={'category_dict': {'$exists': 'true'}})
    category_dict = data['category_dict']

    category_list = []
    for key in category_dict:
        category_list.append(key)
    return category_list

def get_monitoring_data_list(page=1, sort=None, keyword=None):
    if sort is None:
        sort = [('timestamp', -1)]
    per_page = page_default['per_page']
    offset = (page - 1) * per_page
    collection = db['kakao']
    if keyword:
        data_list = collection.find({'msg':{'$regex':keyword}}, sort=sort).limit(per_page).skip(offset)
    else:
        data_list = collection.find(sort=sort).limit(per_page).skip(offset)
    count = data_list.count()
    paging = paginate(page, per_page, count)
    return paging, data_list

def post_monitoring(timestamp=None, category=None):
    collection = db['kakao']
    collection.update_one({'timestamp':timestamp}, {'$set': {'category':category}})

def get_statistics_list(page=1, sort=None):
    if sort is None:
        sort = [('date', -1)]
    per_page = page_default['per_page']
    offset = (page - 1) * per_page

    today = datetime.date.today()
    while True:
        collection = db['kakao']
        str_today = str(today)
        today_find = collection.find({'timestamp':{'$regex':str_today}})
        count = today_find.count()
        if count:
            count, unknown, no_decision, deep_accuracy, bay_accuracy = calculate_accuracy(count, today_find)
            data = {'date':str_today, 'count':count, 'unknown':unknown, 'no_decision':no_decision, 'deep_accuracy':deep_accuracy, 'bay_accuracy':bay_accuracy}
            collection = db['statistics']
            collection.update_one({'date':str_today}, {'$set':data}, upsert=True)
        else:
            break
        today = today - datetime.timedelta(days=1)
    collection = db['statistics']
    count = collection.count()
    data_list = collection.find(sort=sort).limit(per_page).skip(offset)
    paging = paginate(page, per_page, count)
    return paging, data_list

