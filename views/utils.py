import requests
import datetime

# database
from pymongo import MongoClient
mongoClient = MongoClient('mongodb://localhost:27017/')
db = mongoClient['chatbot']

def dbWrite(msg, spacetext, corpus, words, deepScore, bayScore):
    data = {'timestamp': datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S'),
               'msg': msg,
               'spacetext': spacetext,
               'corpus': corpus,
               'words': words,
               'deep': deepScore,
               'bay': bayScore,
               }
    collection = db['kakao']
    collection.insert(data)

def _request_data(verb, url, params=None, headers=None, data=None, stream=False):
    try:
        if data is not None:
            r = requests.request(verb, url, params=params, headers=headers, json=data, timeout=3.0)
        else:
            r = requests.request(verb, url, params=params, headers=headers, timeout=3.0)
    except Exception as e:
        print(e)
        return None
    else:
        if r.status_code == 200 or r.status_code == 201:
            return r.content
        else:
            print(r.status_code, data)
            return None