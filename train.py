import numpy as np
import time

# learning
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import to_categorical
import tensorflow as tf
from predictions.pipeline import LoadModel
from predictions.deep_model import IntentModel
from predictions.bayesianFilter import BayesianFilter
from predictions.preProcess import PreProcess
from models import get_post_nlp, get_nlp_msg, post_prewordCount, post_bayesian, post_deepmodel, post_nlp_wrong

def paraSaveAndTest(filter=None, preProcessing=None):

    # parameter database 저장
    nlp_start_time = time.time()
    intent_total_count, intent_train, label_train, label_idx, idx_label = get_post_nlp(filter=filter, preProcessing=preProcessing)
    nlp_time = time.time() - nlp_start_time
    word_difference = post_bayesian(filter=filter)
    post_prewordCount(preProcessing=preProcessing)
    return intent_total_count, intent_train, label_train, label_idx, idx_label, word_difference, nlp_time

def test_prediction(preProcessing=None):
    loadModel = LoadModel()
    msg_list = get_nlp_msg()
    wrong_nlp_list = []
    for msg, intent in msg_list:
        spacetext, corpus, words = preProcessing.split(msg)
        deepScore = loadModel.deepPrediction(words)
        if deepScore[0][0] != intent:
            wrong_nlp_list.append({'msg':msg, 'spacetext':spacetext, 'corpus':corpus, 'words':words, 'deep':deepScore, 'intent':intent})
    post_nlp_wrong(wrong_nlp_list)

def predict_bayesian(intent_total_count, intent_train, filter=None):
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
            pass
            #print(intent, bayScore, words)
    print('precision ', precision / intent_total_count, pre2 / intent_total_count, pre1 / intent_total_count)

if __name__ == '__main__' :

    # when training, train = True
    start_time = time.time()
    train = True

    preProcessing = PreProcess(train=train)
    bf = BayesianFilter(train=train)

    intent_total_count, intent_train, label_train, label_idx, idx_label, word_difference, nlp_time = paraSaveAndTest(filter=bf, preProcessing=preProcessing)
    # category_dict
    print(bf.category_dict)
    predict_bayesian(intent_total_count, intent_train, filter=bf)

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

    max_len_list = [max_len]
    post_deepmodel(word_index, idx_label, max_len_list)

    test_prediction(preProcessing=preProcessing)
    
    print(word_index)
    print('-----------------------')
    print('word_difference')
    print(word_difference)
    print('-----------------------')
    print('nlp time', nlp_time)
    print('total time', time.time() - start_time)





