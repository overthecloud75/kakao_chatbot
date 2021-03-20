import math, sys
from konlpy.tag import Okt
from pykospacing.kospacing import PredSpacing
# from chatspace import ChatSpace
import json
import re

import numpy as np
import csv
import datetime

from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Embedding, Dropout, Conv1D, GlobalMaxPooling1D, Dense, Input, Flatten, Concatenate
from tensorflow.keras.utils import to_categorical
import tensorflow as tf

han = re.compile('[ㄱ-ㅎㅏ-ㅣ]+')
eng = re.compile('[a-zA-Z]+')
twitter = Okt()

def openText():
    with open('synonym.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        synonym = {}
        for line in lines:
            line = line.split(',')
            line[1] = line[1].strip()
            synonym[line[0]] = line[1]

    with open('stopwords.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        stopwords = []
        for line in lines:
            line = line.split(',')
            line[0] = line[0].strip()
            stopwords.append(line[0])

    with open('custom_vocab.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        custom_vocab = []
        for line in lines:
            line = line.split(',')
            line[0] = line[0].strip()
            custom_vocab.append(line[0])

    with open('split.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        split_words = {}
        for line in lines:
            line = line.split(',')
            line[1] = line[1].strip()
            split_words[line[0]] = line[1]
    return synonym, stopwords, custom_vocab, split_words

def paraSaveAndTest(para=False, filter=None):

    intent_train = []
    label_train = []
    label_idx = {}
    idx_label = {}

    if not para:
        with open('bay.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                line = line.split(',')
                line[1] = line[1].strip()
                filter.fit(line[0], line[1])

                if line[1] in label_idx:
                    idx = label_idx[line[1]]
                    label_train.append(idx)
                else:
                    idx_label[len(label_idx)] = line[1]
                    label_idx[line[1]] = len(label_idx)
                    idx = label_idx[line[1]]
                    label_train.append(idx)

                _, _, seperated = filter.split(line[0])

                intent_train.append(seperated)

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
            f.write('\n')
            f.write(json.dumps(filter.synonym))
            f.write('\n')
            f.write(json.dumps(filter.stopwords))
            f.write('\n')
            f.write(json.dumps(filter.custom_vocab))
            f.write('\n')
            f.write(json.dumps(filter.split_words))

        with open('bay.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            pre1 = 0
            pre2 = 0
            precision = 0
            total = len(lines)

            csvdatalist = []

            for line in lines:
                line = line.split(',')
                line[1] = line[1].strip()
                spacetext, malist, pre, scorelist, words = filter.predict(line[0])
                if line[1] == scorelist[0][0]:
                    pre1 = pre1 + 1
                    pre2 = pre2 + 1
                    precision = precision + 1
                elif line[1] == scorelist[1][0]:
                    pre2 = pre2 + 1
                    precision = precision + 1
                elif line[1] == scorelist[2][0]:
                    precision = precision + 1
                else:
                    print(line[1], scorelist, words, line[0])
                csvdatalist.append([line[0], spacetext, malist, words])
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

class BayesianFilter:
    def __init__(self, para=False, synonym=None, stopwords=[], custom_vocab=[], split_words=None):
        # self.spacer = ChatSpace()
        self.spacer = PredSpacing()
        self.para = para
        if synonym:
            self.synonym = synonym
        if stopwords:
            self.stopwords = stopwords
        if custom_vocab:
            self.custom_vocab = custom_vocab
        if split_words:
            self.split_words = split_words
        if para:
            setJason = []
            with open('para.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    setJason.append(json.loads(line))

            self.words = set(setJason[0])
            self.word_dict = setJason[1]
            self.category_dict = setJason[2]
            self.word_count = setJason[3]
            self.synonym = setJason[4]
            self.stopwords = setJason[5]
            self.custom_vocab = setJason[6]
            self.split_words = setJason[7]
        else:
            self.words = set()
            self.word_dict = {}
            self.category_dict = {}
            self.word_count = {}

    def pre_text(self, text, pre=True):
        spacetext = None
        if pre:
            #text = self.spacer.space(text, custom_vocab=self.custom_vocab)
            #text = spacing(text)
            text = self.spacer.spacing(text)
            spacetext = text
            split_text = text.split(' ')
            fix_text = ''
            for word in split_text:
                fix_split = False
                for split_word in self.split_words:
                    if split_word in word:
                        if fix_text == '':
                            fix_text = self.split_words[split_word]
                        else:
                            fix_text = fix_text + ' ' + self.split_words[split_word]
                        fix_split = True
                        break
                if not fix_split:
                    if fix_text == '':
                        fix_text = word
                    else:
                        fix_text = fix_text + ' ' + word
        else:
            fix_text = []
            for word in text:
                if word in self.split_words:
                    fix_text = fix_text + self.split_words[word].split(' ')
                else:
                    fix_text.append(word)
        return spacetext, fix_text

    def split(self, text):
        results = []
        spacetext, text = self.pre_text(text)
        malist = twitter.pos(text, norm=True, stem=True)
        for word in malist:
            if not word[1] in ['Josa', 'Eomi', 'Punctuation'] and not word[0] == '\n' and not word[0] == '\n\n':
                word0 = word[0]
                if eng.match(word0):
                    word0 = word0.lower()
                if word0 in self.synonym:
                    word0 = self.synonym[word0]
                if han.match(word0):
                    pass
                else:
                    results.append(word0)
            else:
                if word[1] == 'Punctuation' and word[0] == '?':
                    results.append(word[0])
        _, results = self.pre_text(results, pre=False)
        new_results = self.custom(results)
        return spacetext, malist, new_results

    def custom(self, results):
        len_result = len(results)
        new_results = []
        add = 0
        if len_result > 1:
            for i in range(len_result):
                if add > 0:
                    add = add - 1
                elif i < len_result - 1 and results[i] + results[i + 1] in self.custom_vocab:
                    word = results[i] + results[i + 1]
                    if word in self.synonym:
                        word = self.synonym[word]
                    if self.para and word not in self.word_count and word not in self.synonym:
                        print('not self.world_count', word)
                        pass
                    elif word in self.stopwords:
                        pass
                    else:
                        new_results.append(word)
                    add = 1
                elif i < len_result - 2 and results[i] + results[i + 1] + results[i + 2] in self.custom_vocab:
                    word = results[i] + results[i + 1] + results[i + 2]
                    if word in self.synonym:
                        word = self.synonym[word]
                    if self.para and word not in self.word_count and word not in self.synonym:
                        print('not self.world_count', word)
                        pass
                    elif word in self.stopwords:
                        pass
                    else:
                        new_results.append(word)
                    add = 2
                elif i < len_result - 3 and results[i] + results[i + 1] + results[i + 2] + results[
                    i + 3] in self.custom_vocab:
                    word = results[i] + results[i + 1] + results[i + 2] + results[i + 3]
                    if word in self.synonym:
                        word = self.synonym[word]
                    if self.para and word not in self.word_count and word not in self.synonym:
                        print('not self.world_count', word)
                        pass
                    elif word in self.stopwords:
                        pass
                    else:
                        new_results.append(word)
                    add = 3
                else:
                    word = results[i]
                    if word in self.synonym:
                        word = self.synonym[word]
                    if self.para and word not in self.word_count and word not in self.synonym:
                        print('not self.world_count', word)
                        pass
                    elif word in self.stopwords:
                        pass
                    else:
                        new_results.append(word)
        else:
            for word in results:
                if word in self.synonym:
                    word = self.synonym[word]
                if self.para and word not in self.word_count and word not in self.synonym:
                    print('not self.world_count', word)
                    pass
                elif word in self.stopwords:
                    pass
                else:
                    new_results.append(word)
        return new_results

    def inc_word(self, word, category):
        if not category in self.word_dict:
            self.word_dict[category] = {}
        if not word in self.word_dict[category]:
            self.word_dict[category][word] = 0
        self.word_dict[category][word] += 1
        self.words.add(word)

    def inc_category(self, category):
        if category not in self.category_dict:
            self.category_dict[category] = 0
        self.category_dict[category] += 1

    def fit(self, text, category):
        _, _, word_list = self.split(text)
        for word in word_list:
            self.inc_word(word, category)
        self.inc_category(category)

    def score(self, words, category):
        score = math.log(self.category_prob(category))
        for word in words:
            score += math.log(self.word_prob(word, category))
        return score

    def predict(self, text):
        best_category = None
        max_score = -sys.maxsize
        spacetext, malist, words = self.split(text)
        score_list = []
        for category in self.category_dict.keys():
            score = self.score(words, category)
            score_list.append((category, score))
            if score > max_score:
                max_score = score
                best_category = category
        score_list = sorted(score_list, key=lambda i: i[1]) #score_list 정렬
        score_list.reverse()
        return spacetext, malist, best_category, score_list[0:3], words

    def get_word_count(self, word, category):
        if word in self.word_dict[category]:
            return self.word_dict[category][word]
        else:
            return 0

    def category_prob(self, category):
        sum_categories = sum(self.category_dict.values())
        category_v = self.category_dict[category]
        return category_v / sum_categories

    def word_prob(self, word, category):
        n = self.get_word_count(word, category) + 1
        d = sum(self.word_dict[category].values()) + len(self.words)
        return n / d

    def get_total_word_count(self):
        for category in self.word_dict:
            for word in self.word_dict[category]:
                if word not in self.word_count:
                    self.word_count[word] = self.word_dict[category][word]
                else:
                    self.word_count[word] = self.word_count[word] + self.word_dict[category][word]
        return self.word_count

class IntentModel:
    def __init__(self, max_len=22, vocab_size=400, filter_sizes=[2,3,5], embedding_dim=16, num_filters=32, drop=0.5, len_label=70):
        self.max_len=max_len
        self.vocab_size = vocab_size
        self.filter_sizes = filter_sizes
        self.embedding_dim = embedding_dim
        self.num_filters = num_filters
        self.drop = drop
        self.len_label=len_label

    def create_model(self):
        model_input = Input(shape=(self.max_len,))
        z = Embedding(self.vocab_size, self.embedding_dim, input_length=self.max_len)(model_input)

        conv_blocks = []

        for sz in self.filter_sizes:
            conv = Conv1D(filters=self.num_filters,
                          kernel_size=sz,
                          padding="valid",
                          activation="relu",
                          strides=1)(z)
            conv = GlobalMaxPooling1D()(conv)
            conv = Flatten()(conv)
            conv_blocks.append(conv)

        z = Concatenate()(conv_blocks) if len(conv_blocks) > 1 else conv_blocks[0]
        z = Dropout(self.drop)(z)
        model_output = Dense(self.len_label, activation='softmax')(z)

        model = Model(model_input, model_output)
        model.summary()

        model.compile(loss='categorical_crossentropy',
                      optimizer='adam',
                      metrics=['acc'])
        return model

if __name__ == '__main__' :

    synonym, stopwords, custom_vocab, split_words = openText()

    para = False  # 훈련할 때 para = False
    bf = BayesianFilter(para=para, synonym=synonym, stopwords=stopwords, custom_vocab=custom_vocab, split_words=split_words)

    intent_train, label_train, label_idx, idx_label, csvdatalist = paraSaveAndTest(para=para, filter=bf)

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





