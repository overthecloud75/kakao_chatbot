from pymongo import MongoClient

# database
mongoClient = MongoClient('mongodb://localhost:27017/')
db = mongoClient['chatbot']
collection = db['intent']

with open('bay.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for line in lines:
        line = line.split(',')
        intent_msg = {'msg': line[0], 'intent':line[1].strip()}
        collection.update_one(intent_msg, {'$set': intent_msg}, upsert=True)


