import json

import numpy as np
import csv
import datetime

# learning
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import to_categorical
import tensorflow as tf
from models.deep_model import IntentModel
from models.bayesianFilter import BayesianFilter
from models.preProcess import PreProcess

# database
from pymongo import MongoClient
mongoClient = MongoClient('mongodb://localhost:27017/')
db = mongoClient['chatbot']

def paraSaveAndTest(para=False, filter=None, preProcessing=None):

    intent_train = []
    label_train = []
    label_idx = {}
    idx_label = {}

    csvdatalist = []

    if not para:
        collection = db['intent']
        finds = collection.find(filter={})
        total = collection.count_documents({})
        for find in finds:
            msg = find['msg']
            intent = find['intent']
            if intent in label_idx:
                idx = label_idx[intent]
                label_train.append(idx)
            else:
                idx_label[len(label_idx)] = intent
                label_idx[intent] = len(label_idx)
                idx = label_idx[intent]
                label_train.append(idx)

            spacetext, corpus, words = preProcessing.split(msg)
            filter.fit(words, intent)
            csvdatalist.append([msg, spacetext, corpus, words, intent])
            intent_train.append(words)

        print(filter.category_dict)
       # parameter 저장
        with open('para.txt', 'w', encoding='utf-8') as f:
            f.write(json.dumps(list(filter.words)))
            f.write('\n')
            f.write(json.dumps(filter.word_dict))
            f.write('\n')
            f.write(json.dumps(filter.category_dict))
            f.write('\n')
            f.write(json.dumps(filter.get_total_word_count()))

        pre1 = 0
        pre2 = 0
        precision = 0

        for i, words in enumerate(intent_train):
            bayScore = filter.predict(words)
            intent = idx_label[label_train[i]]
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

    return intent_train, label_train, label_idx, idx_label, csvdatalist

def modelParaSave(word_index, idx_label, max_len_list):
    with open('model.txt', 'w', encoding='utf-8') as f:
        print(word_index)
        f.write(json.dumps(word_index))
        f.write('\n')
        f.write(json.dumps(idx_label))
        f.write('\n')
        f.write(json.dumps(max_len_list))

def csvWrite():
    f = open('kon.csv', 'a', encoding='utf-8-sig', newline='')
    wr = csv.writer(f)
    for data in csvdatalist:
        add = [datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S'), data[0], data[1], data[2], data[3]]
        wr.writerow(add)
    f.close()

if __name__ == '__main__' :

    # when training, para = False
    para = False

    preProcessing = PreProcess(para=para)
    bf = BayesianFilter(para=para)

    intent_train, label_train, label_idx, idx_label, csvdatalist = paraSaveAndTest(para=para, filter=bf, preProcessing=preProcessing)

    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(intent_train)
    sequences = tokenizer.texts_to_sequences(intent_train)

    word_index = tokenizer.word_index
    index_word = tokenizer.index_word
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

    model.save('intent.h5')

    model = tf.keras.models.load_model('intent.h5')
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
    modelParaSave(word_index, idx_label, max_len_list)

    csvWrite()





