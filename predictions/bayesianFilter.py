import math
import json

# database
from pymongo import MongoClient
mongoClient = MongoClient('mongodb://localhost:27017/')
db = mongoClient['chatbot']

class BayesianFilter:
    def __init__(self, para=False):
        if para:

            collection = db['bayesian']

            data = collection.find_one(filter={'words':{'$exists':'true'}})
            self.words = data['words']
            data = collection.find_one(filter={'word_dict':{'$exists':'true'}})
            self.word_dict = data['word_dict']
            data = collection.find_one(filter={'category_dict':{'$exists':'true'}})
            self.category_dict = data['category_dict']
            data = collection.find_one(filter={'word_count':{'$exists':'true'}})
            self.word_count = data['word_count']
        else:
            self.words = set()
            self.word_dict = {}
            self.category_dict = {}
            self.word_count = {}

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

    def fit(self, words, category):
        for word in words:
            self.inc_word(word, category)
        self.inc_category(category)

    def score(self, words, category):
        score = math.log(self.category_prob(category))
        for word in words:
            score += math.log(self.word_prob(word, category))
        return score

    def predict(self, words):
        score_list = []
        for category in self.category_dict.keys():
            score = self.score(words, category)
            score_list.append((category, score))
        score_list = sorted(score_list, key=lambda i: i[1]) # sort score_list
        score_list.reverse()
        return score_list[0:3]

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