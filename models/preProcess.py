from konlpy.tag import Okt
from pykospacing.kospacing import PredSpacing
# from chatspace import ChatSpace
import json

import re

han = re.compile('[ㄱ-ㅎㅏ-ㅣ]+')
eng = re.compile('[a-zA-Z]+')
twitter = Okt()

class PreProcess:
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
            self.word_count = setJason[3]
            self.synonym = setJason[4]
            self.stopwords = setJason[5]
            self.custom_vocab = setJason[6]
            self.split_words = setJason[7]
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