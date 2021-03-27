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

def openText():
    collection = db['preprocess']
    with open('synonym.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        synonym = {}
        for line in lines:
            line = line.split(',')
            line[1] = line[1].strip()
            synonym[line[0]] = line[1]
            update = {'type':'synonym', 'word':line[0], 'sub':line[1]}
            collection.update_one({'type':'synonym', 'word':line[0]}, {'$set': update}, upsert=True)

    with open('stopwords.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        stopwords = []
        for line in lines:
            line = line.split(',')
            line[0] = line[0].strip()
            stopwords.append(line[0])
            update = {'type': 'stopwords', 'word': line[0]}
            collection.update_one({'type':'stopwords', 'word':line[0]}, {'$set':update}, upsert=True)

    with open('custom_vocab.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        custom_vocab = []
        for line in lines:
            line = line.split(',')
            line[0] = line[0].strip()
            custom_vocab.append(line[0])
            update = {'type':'custom_vocab', 'word':line[0]}
            collection.update_one({'type':'custom_vocab', 'word':line[0]}, {'$set':update}, upsert=True)

    with open('split.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        split_words = {}
        for line in lines:
            line = line.split(',')
            line[1] = line[1].strip()
            split_words[line[0]] = line[1]
            update = {'type':'split', 'word':line[0], 'sub':line[1]}
            collection.update_one({'type':'split', 'word':line[0]}, {'$set':update}, upsert=True)
    return synonym, stopwords, custom_vocab, split_words

openText()


