import datetime
from views.config import page_default
from utils import calculate_accuracy
from pymongo import MongoClient

mongoClient = MongoClient('mongodb://localhost:27017/')
db = mongoClient['chatbot']

def get_category_list():
    collection = db['bayesian']
    data = collection.find_one(filter={'category_dict': {'$exists': 'true'}})
    category_dict = data['category_dict']

    category_list = []
    for key in category_dict:
        category_list.append(key)
    return category_list

def get_intent_list():
    collection = db['bayesian']
    data = collection.find_one(filter={'category_dict': {'$exists': 'true'}})
    category_dict = data['category_dict']

    intent_list = []
    for key in category_dict:
        intent = {'intent':key, 'count':category_dict[key]}
        intent_list.append(intent)
    return intent_list

def get_intent_paging(intent_list, page=1):
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
    collection = db['intent']
    collection.update_one(request_data, {'$set':request_data}, upsert=True)

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

def get_monitoring_data_list(page=1, sort='timestamp'):
    per_page = page_default['per_page']
    offset = (page - 1) * per_page
    collection = db['kakao']
    count = collection.count()
    data_list = collection.find(sort=[(sort, -1)]).limit(per_page).skip(offset)
    paging = paginate(page, per_page, count)
    return paging, data_list

def post_monitoring(timestamp=None, category=None):
    collection = db['kakao']
    collection.update_one({'timestamp':timestamp}, {'$set': {'category':category}})

def get_statistics_list(page=1, sort='date'):
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
    data_list = collection.find(sort=[(sort, -1)]).limit(per_page).skip(offset)
    paging = paginate(page, per_page, count)
    return paging, data_list

def paginate(page, per_page, count):
    offset = (page - 1) * per_page
    total_page = int(count / per_page) + 1
    paging = {'page':page,
              'has_prev':True,
              'has_next':True,
              'prev_num':page-1,
              'next_num':page+1,
              'count': count,
              'offset':offset,
              'pages':[x + 1  for x in range(total_page)]
              }
    if page == 1:
        paging['has_prev'] = False
    if offset > count or offset + per_page > count:
        paging['has_next'] = False
    return paging