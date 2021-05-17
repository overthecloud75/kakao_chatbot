from konlpy.tag import Okt
from pykospacing.kospacing import PredSpacing
# from chatspace import ChatSpace

import re

# database
from pymongo import MongoClient
mongoClient = MongoClient('mongodb://localhost:27017/')
db = mongoClient['chatbot']

han = re.compile('[ㄱ-ㅎㅏ-ㅣ]+')
eng = re.compile('[a-zA-Z]+')
twitter = Okt()

def openText():
    collection = db['preprocess']
    synonym = {}
    data_list = collection.find({'type':'synonym'})
    for data in data_list:
        synonym[data['word']] = data['sub']
    stopwords = []
    data_list = collection.find({'type':'stopwords'})
    for data in data_list:
        stopwords.append(data['word'])

    custom_vocab = []
    data_list = collection.find({'type':'custom_vocab'})
    for data in data_list:
        custom_vocab.append(data['word'])

    split_words = {}
    data_list = collection.find({'type':'split'})
    for data in data_list:
        split_words[data['word']] = data['sub']
    return synonym, stopwords, custom_vocab, split_words

class PreProcess:
    def __init__(self, para=False):
        # self.spacer = ChatSpace()
        self.spacer = PredSpacing()
        self.para = para

        self.synonym, self.stopwords, self.custom_vocab, self.split_words = openText()
        if para:
            collection = db['bayesian']
            word_count = {}
            data_list = collection.find({'type':'word_count'})
            for data in data_list:
                word_count[data['word']] = data['count']
            self.word_count = word_count
        else:
            self.word_count = {}

    def pre_text(self, text, pre=True):
        spacetext = None
        if pre:
            #text = self.spacer.space(text, custom_vocab=self.custom_vocab)
            #text = spacing(text)
            spacetext = text.split(' ')
            new_text = ''

            for word in spacetext:
                if word in self.synonym:               # 오타 수정
                    word = self.synonym[word]
                if word in self.split_words:           # 뛰어 쓰기 안 되는 것에 대한 뛰어 쓰기 진행
                    word = self.split_words[word]
                if new_text == '':
                    new_text = word
                else:
                    new_text = new_text + ' ' + word

            new_text = self.spacer.spacing(new_text)
            spacetext = new_text
        else:
            new_text = []
            for word in text:
                if word in self.split_words:
                    new_text = new_text + self.split_words[word].split(' ')
                else:
                    new_text.append(word)
        return spacetext, new_text

    def split(self, text):
        results = []
        spacetext, text = self.pre_text(text)  # 뛰워쓰기 및 오타 수정
        corpus = twitter.pos(text, norm=True, stem=True)
        for word in corpus:
            if not word[1] in ['Josa', 'Eomi', 'Punctuation'] and not word[0] == '\n' and not word[0] == '\n\n':
                word0 = word[0]
                if eng.match(word0):
                    word0 = word0.lower()
                if han.match(word0):
                    pass
                else:
                    results.append(word0)
            else:
                if word[1] == 'Punctuation' and word[0] == '?':
                    results.append(word[0])
        _, results = self.pre_text(results, pre=False)
        new_results = self.custom(results)
        return spacetext, corpus, new_results

    def custom(self, results):
        len_result = len(results)
        new_results = []
        add = 0
        if len_result > 1:
            for i in range(len_result):
                if add > 0:
                    add = add - 1
                elif i < len_result - 3 and results[i] + results[i + 1] + results[i + 2] + results[i + 3] in self.custom_vocab:
                    word = results[i] + results[i + 1] + results[i + 2] + results[i + 3]
                    if word in self.synonym:
                        word = self.synonym[word]
                    if self.para and word not in self.word_count and word not in self.synonym:
                        print('not self.world_count', word)
                        pass
                    elif word in self.stopwords:
                        pass
                    else:
                        if word in self.split_words:
                            split_words = self.split_words[word].split(' ')
                            for w in split_words:
                                new_results.append(w)
                        else:
                            new_results.append(word)
                    add = 3
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
                        if word in self.split_words:
                            split_words = self.split_words[word].split(' ')
                            for w in split_words:
                                new_results.append(w)
                        else:
                            new_results.append(word)
                    add = 2
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
                        if word in self.split_words:
                            split_words = self.split_words[word].split(' ')
                            for w in split_words:
                                new_results.append(w)
                        else:
                            new_results.append(word)
                    add = 1
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
                        if word in self.split_words:
                            split_words = self.split_words[word].split(' ')
                            for w in split_words:
                                new_results.append(w)
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
                    if word in self.split_words:
                        split_words = self.split_words[word].split(' ')
                        for w in split_words:
                            new_results.append(w)
                    else:
                        new_results.append(word)
        return new_results