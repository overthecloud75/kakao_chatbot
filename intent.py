from pymongo import MongoClient

# database
mongoClient = MongoClient('mongodb://localhost:27017/')
db = mongoClient['chatbot']
# collection = db['intent']

'''with open('bay.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for line in lines:
        line = line.split(',')
        intent_msg = {'msg': line[0], 'intent':line[1].strip()}
        collection.update_one(intent_msg, {'$set': intent_msg}, upsert=True)'''

'''collection = db['kakao']
data = collection.find({})
for date in data:
    # timestamp = data['timestamp']
    timestamp = date['timestamp'].split(' ')
    print(timestamp)
    timesplit = timestamp[0].split(',')[0]
    timesplit = timesplit.split('/')
    year = timesplit[2]
    month = timesplit[0]
    day = timesplit[1]
    new_timestamp = year + '-' + month + '-' + day + ' ' + timestamp[1]
    print(new_timestamp, date['timestamp'])

    collection.update_one({'timestamp':date['timestamp']}, {'$set': {'timestamp':new_timestamp}})'''



