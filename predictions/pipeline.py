import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
from models import set_deep

class LoadModel:
    def __init__(self):
        # dnn model parameter 열기
        try:
            self.model = tf.keras.models.load_model('predictions/intent.h5')
        except Exception as e:
            print(e)
            self.model = None
        self.word_index, self.idx_label, self.max_len = set_deep()

    def deepPrediction(self, words):
        sentence = []
        for word in words:
            sentence.append(self.word_index[word])
        x = pad_sequences([sentence], maxlen=self.max_len)

        # https://www.tensorflow.org/api_docs/python/tf/keras/preprocessing/sequence/pad_sequences
        # tf.keras.preprocessing.sequence.pad_sequences(sequence, maxlen=2)
        # array([[0, 1], [2, 3], [5, 6]])

        y = self.model.predict(x)
        y = tf.nn.softmax(y).numpy().tolist()[0]

        score_list = []
        for idx in self.idx_label:
            score_list.append((self.idx_label[str(idx)], y[int(idx)]))
        score_list = sorted(score_list, key=lambda i: i[1])
        score_list.reverse()
        return score_list[0:3]