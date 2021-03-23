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

class PreProcess:
    def __init__(self, para=False):
        # self.spacer = ChatSpace()
        self.spacer = PredSpacing()
        self.para = para

        self.synonym, self.stopwords, self.custom_vocab, self.split_words = openText()
        if para:
            collection = db['bayesian']
            data = collection.find_one(filter={'word_count': {'$exists': 'true'}})
            self.word_count = data['word_count']
        else:
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
        corpus = twitter.pos(text, norm=True, stem=True)
        for word in corpus:
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
        return spacetext, corpus, new_results

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