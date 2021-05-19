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
    typo = {}
    typo_count = {}
    data_list = collection.find({'type':'typo'})
    for data in data_list:
        typo[data['word']] = data['sub']
        typo_count[data['sub']] = 0

    synonym = {}
    synonym_count = {}
    data_list = collection.find({'type':'synonym'})
    for data in data_list:
        synonym[data['word']] = data['sub']
        synonym_count[data['sub']] = 0

    stopwords = []
    stopwords_count = {}
    data_list = collection.find({'type':'stopwords'})
    for data in data_list:
        stopwords.append(data['word'])
        stopwords_count[data['word']] = 0

    custom_vocab = []
    custom_vocab_count = {}
    data_list = collection.find({'type':'custom_vocab'})
    for data in data_list:
        custom_vocab.append(data['word'])
        custom_vocab_count[data['word']] = 0

    split_words = {}
    split_words_count = {}
    data_list = collection.find({'type':'split'})
    for data in data_list:
        split_words[data['word']] = data['sub']
        split_words_count[data['sub']] = 0
    return typo, typo_count, synonym, synonym_count, stopwords, stopwords_count, custom_vocab, custom_vocab_count, split_words, split_words_count

class PreProcess:
    def __init__(self, train=False):
        # self.spacer = ChatSpace()
        self.spacer = PredSpacing()
        self.train = train

        self.typo, self.typo_count, self.synonym, self.synonym_count, self.stopwords, self.stopwords_count, \
        self.custom_vocab, self.custom_vocab_count, self.split_words, self.split_words_count = openText()
        if not self.train:
            collection = db['bayesian']
            word_count = {}
            data_list = collection.find({'type':'word_count'})
            for data in data_list:
                word_count[data['word']] = data['count']
            self.word_count = word_count
        else:
            self.word_count = {}

    def pre_text(self, text, pre=True):
        if pre:
            #text = self.spacer.space(text, custom_vocab=self.custom_vocab)
            #text = spacing(text)
            text = text.lower()
            text = self.typo_correction(text)
            text = self.spacer.spacing(text)
            text = self.split_correction(text)
            return text
        else:
            results = []
            for word in text:
                word_list = self.split_matching(word)
                results = results + word_list
            return results

    def split(self, text):
        results = []
        text = self.pre_text(text)  # 뛰워쓰기 및 오타 수정
        corpus = twitter.pos(text, norm=True, stem=True)
        corpus = self.custom_corpus(corpus)
        for word in corpus:
            if not word[1] in ['Josa', 'Eomi', 'Punctuation'] and not word[0] == '\n' and not word[0] == '\n\n':
                word0 = word[0]
                if han.match(word0):
                    pass
                else:
                    results.append(word0)
            else:
                if word[1] == 'Punctuation' and word[0] == '?':
                    results.append(word[0])
        results = self.pre_text(results, pre=False)
        results = self.custom(results)
        return text, corpus, results

    def custom_corpus(self, corpus):
        word_list = corpus
        len_result = len(word_list)
        new_corpus = []
        add = 0
        if len_result > 0:
            for i in range(len_result):
                if add > 0:
                    add = add - 1
                    word = None
                elif i < len_result - 3 and word_list[i][0] + word_list[i + 1][0] + word_list[i + 2][0] + word_list[i + 3][0] in self.custom_vocab:
                    word = [word_list[i][0] + word_list[i + 1][0] + word_list[i + 2][0] + word_list[i + 3][0], 'Noun']
                    add = 3
                    if self.train:
                        self.custom_vocab_count[word[0]] = self.custom_vocab_count[word[0]] + 1
                elif i < len_result - 2 and word_list[i][0] + word_list[i + 1][0] + word_list[i + 2][0] in self.custom_vocab:
                    word = [word_list[i][0] + word_list[i + 1][0] + word_list[i + 2][0], 'Noun']
                    add = 2
                    if self.train:
                        self.custom_vocab_count[word[0]] = self.custom_vocab_count[word[0]] + 1
                elif i < len_result - 1 and word_list[i][0] + word_list[i + 1][0] in self.custom_vocab:
                    word = [word_list[i][0] + word_list[i + 1][0], 'Noun']
                    add = 1
                    if self.train:
                        self.custom_vocab_count[word[0]] = self.custom_vocab_count[word[0]] + 1
                else:
                    word = word_list[i]
                if word is not None:
                    new_corpus.append(word)
        return new_corpus

    def custom(self, results):
        len_result = len(results)
        new_results = []
        add = 0
        if len_result > 0:
            for i in range(len_result):
                if add > 0:
                    add = add - 1
                elif i < len_result - 3 and results[i] + results[i + 1] + results[i + 2] + results[i + 3] in self.custom_vocab:
                    word = results[i] + results[i + 1] + results[i + 2] + results[i + 3]
                    word_list = self.custom_correction(word, custom=True)
                    for word in word_list:
                        new_results.append(word)
                    add = 3
                elif i < len_result - 2 and results[i] + results[i + 1] + results[i + 2] in self.custom_vocab:
                    word = results[i] + results[i + 1] + results[i + 2]
                    word_list = self.custom_correction(word, custom=True)
                    for word in word_list:
                        new_results.append(word)
                    add = 2
                elif i < len_result - 1 and results[i] + results[i + 1] in self.custom_vocab:
                    word = results[i] + results[i + 1]
                    word_list = self.custom_correction(word, custom=True)
                    for word in word_list:
                        new_results.append(word)
                    add = 1
                else:
                    word = results[i]
                    word_list = self.custom_correction(word)
                    for word in word_list:
                        new_results.append(word)
        return new_results

    def typo_correction(self, text):
        word_list = text.split(' ')
        text = ''
        for word in word_list:
            for typo in self.typo:
                if typo in word:
                    word = re.sub(typo, self.typo[typo], word)
                    if self.train:
                        self.typo_count[self.typo[typo]] = self.typo_count[self.typo[typo]] + 1
                    break
            if text == '':
                text = word
            else:
                text = text + ' ' + word
        return text

    def split_correction(self, text):
        word_list = text.split(' ')
        text = ''
        for word in word_list:
            for split in self.split_words:
                if split in word:
                    word = re.sub(split, self.split_words[split], word)
                    if self.train:
                        self.split_words_count[self.split_words[split]] = self.split_words_count[
                                                                              self.split_words[split]] + 1
                    break
            if text == '':
                text = word
            else:
                text = text + ' ' + word
        return text

    def custom_correction(self, word, custom=False):
        if self.train and custom:
            self.custom_vocab_count[word] = self.custom_vocab_count[word] + 1
        if word in self.synonym:
            word = self.synonym[word]
            if self.train:
                self.synonym_count[word] = self.synonym_count[word] + 1
        if not self.train and word not in self.word_count:
            print('not self.world_count', word)
            word_list = []
        elif word in self.stopwords:
            word_list = []
            if self.train:
                self.stopwords_count[word] = self.stopwords_count[word] + 1
        else:
            word_list = self.split_matching(word)
        return word_list

    def split_matching(self, word):
        if word in self.split_words:
            split_words = self.split_words[word].split(' ')
            if self.train:
                self.split_words_count[self.split_words[word]] = self.split_words_count[self.split_words[word]] + 1
        else:
            split_words = word.split(' ')
        return split_words

