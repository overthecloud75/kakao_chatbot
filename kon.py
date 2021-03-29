import numpy as np
import csv
import datetime

# learning
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import to_categorical
import tensorflow as tf
from predictions.deep_model import IntentModel
from predictions.bayesianFilter import BayesianFilter
from predictions.preProcess import PreProcess

# database
from pymongo import MongoClient
mongoClient = MongoClient('mongodb://localhost:27017/')
db = mongoClient['chatbot']

def paraSaveAndTest(para=False, filter=None, preProcessing=None):

    intent_train = []
    label_train = []
    label_idx = {}
    idx_label = {}

    if not para:
        collection = db['intent']
        data_list = collection.find()
        total = collection.count_documents({})
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
            update = {'timestamp':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                      'msg':msg,
                      'spacetext':spacetext,
                      'corpus':corpus,
                      'words': words,
                      'intent':intent}
            collection.update_one({'msg':msg}, {'$set':update}, upsert=True)
            intent_train.append(words)

        print(filter.category_dict)
       # parameter 저장
        db.drop_collection('bayesian')
        collection = db['bayesian']

        for word in list(filter.words):
            update = {'type':'words', 'word':word}
            collection.update_one({'type':'words', 'word':word}, {'$set':update}, upsert=True)
        update = {'word_dict': filter.word_dict}
        collection.update_one({'word_dict':{'$exists':'true'}}, {'$set':update}, upsert=True)
        for key in filter.category_dict:
            update = {'type':'intent', 'intent':key, 'count':filter.category_dict[key]}
            collection.update_one({'type':'intent', 'intent':key}, {'$set':update}, upsert=True)
        word_count = filter.get_total_word_count()
        for key in word_count:
            update = {'type':'word_count', 'word':key, 'count':word_count[key]}
            collection.update_one({'type':'category', 'word':key}, {'$set':update}, upsert=True)

        pre1 = 0
        pre2 = 0
        precision = 0

        for i, words in enumerate(intent_train):
            bayScore = filter.predict(words)
            intent = idx_label[str(label_train[i])]
            if intent == bayScore[0][0]:
                pre1 = pre1 + 1
                pre2 = pre2 + 1
                precision = precision + 1
            elif intent == bayScore[1][0]:
                pre2 = pre2 + 1
                precision = precision + 1
            elif intent == bayScore[2][0]:
                precision = precision + 1
            else:
                print(intent, bayScore, words)
        print('precision ', precision / total, pre2 / total, pre1 / total)
    return intent_train, label_train, label_idx, idx_label

def deepModelParaSave(word_index, index_words, idx_label, max_len_list):
    # How to drop a collection with pymongo?
    # https://stackoverflow.com/questions/48923682/how-to-drop-a-collection-with-pymongo
    # parameter 저장
    db.drop_collection('deep')
    collection = db['deep']
    for word in word_index:
        update = {'type':'word_index', 'word':word, 'idx':word_index[word]}
        collection.update_one({'type':'word_index', 'word':word}, {'$set': update}, upsert=True)
    for word in idx_label:
        update = {'type':'idx_label', 'idx':word, 'label':idx_label[word]}
        collection.update_one({'type':'idx_label', 'idx':word}, {'$set': update}, upsert=True)
    update = {'max_len_list': max_len_list}
    collection.update_one({'max_len_list': {'$exists':'true'}}, {'$set':update}, upsert=True)

if __name__ == '__main__' :

    # when training, para = False
    para = False

    preProcessing = PreProcess(para=para)
    bf = BayesianFilter(para=para)

    intent_train, label_train, label_idx, idx_label = paraSaveAndTest(para=para, filter=bf, preProcessing=preProcessing)

    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(intent_train)
    sequences = tokenizer.texts_to_sequences(intent_train)

    word_index = tokenizer.word_index
    index_word = tokenizer.index_word
    index_words = []
    for key in word_index:
        index_words.append(key)
    vocab_size = len(word_index) + 1

    max_len = max(len(l) for l in sequences)

    intent_train = pad_sequences(sequences, maxlen=max_len)
    label_train = to_categorical(np.asarray(label_train))

    indices = np.arange(intent_train.shape[0])
    np.random.shuffle(indices)

    intent_train = intent_train[indices]
    label_train = label_train[indices]

    intent_model = IntentModel(max_len=max_len, vocab_size=vocab_size, filter_sizes=[2, 3, 5], embedding_dim=16,
                               num_filters=32, drop=0.5, len_label=len(label_idx))
    model = intent_model.create_model()

    history = model.fit(intent_train, label_train,
                        batch_size=16,
                        epochs=100,
                        validation_data=(intent_train, label_train))

    model.save('predictions/intent.h5')
    model = tf.keras.models.load_model('predictions/intent.h5')
    len_intent = intent_train.shape[0]

    k = 0
    deepsocorelist = []
    for i in range(len_intent):
        x = np.expand_dims(intent_train[i], axis=0)
        try:
            y = model(x)
            ax = np.argmax(y)
            ay = np.argmax(label_train[i])
            if ax == ay:
                k = k + 1
        except Exception as e:
            print(e)
            print(x, vocab_size)
            for i in x[0]:
                if i != 0 :
                    print(index_word[i])

    print('precison: %s' %(str(k/len_intent)))
    max_len_list = [max_len]
    deepModelParaSave(word_index, index_words, idx_label, max_len_list)
    print(word_index)





