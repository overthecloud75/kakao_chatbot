from flask import Blueprint, jsonify, request, current_app
import time
import threading

# ocr
from io import BytesIO
import matplotlib
matplotlib.use('agg')
import cv2
try:
    import keras_ocr
    # ocr setting
    pipeline = keras_ocr.pipeline.Pipeline(max_size=700)
    pipe_time = time.time()
except Exception as e:
    pipeline = None
    print(e)

try:
    from .category_config import config_score, config_account, config_system
except Exception as e:
    config_score = {'account':[], 'system':[]}
    config_account = []
    config_system = []

from .response import conditionalCheckIntent, simpleResponse, cardResponse
from models import kakaoWrite
from utils import _request_data

# prediction
from predictions.preProcess import PreProcess
from predictions.bayesianFilter import BayesianFilter
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
from models import set_deep

# blueprint
bp = Blueprint('api', __name__, url_prefix='/api')

# flask setting
userRequest = {}

# bayesianFilter
train = False
preProcessing = PreProcess(train=train)
bf = BayesianFilter(train=train)

# dnn model parameter 열기
model = tf.keras.models.load_model('predictions/intent.h5')
word_index, idx_label, max_len = set_deep()

@bp.route('/',  methods=['GET', 'POST'])
def kakao():
    message = info(request.get_json())
    response = {'version':'2.0', 'template':{}}
    if not message:
        current_app.logger.info('%s - %s - %s - %s' %(request.remote_addr, request.url, threading.current_thread(), message))
        return '', 204
    else:
        current_app.logger.info('%s - %s - %s - %s' %(request.remote_addr, request.url, threading.current_thread(), message['msg']))
        if pipeline and 'http' in message['msg'] and ('.png' in message['msg'] or '.jpg' in message['msg'] or '.jpeg' in message['msg']):
            # image process
            raw_image_url = 'raw_image/' + str(int(time.time())) + '.png'
            img = _request_data('GET', message['msg'])

            img = BytesIO(img)
            img = keras_ocr.tools.read(img)

            start_time = time.time()
            global pipe_time
            if start_time - pipe_time > 15:   #동시에 사진을 여러번 보내는 것을 감지 하기 위해서 있음
                pipe_time = start_time
                prediction = pipeline.recognize([img])
                end_time = time.time()
                current_app.logger.info('%s - %s' %('detection time', end_time - start_time))
                # word extraction
                words = []
                for i in range(len(prediction[0])):
                    if prediction[0][i][0] in preProcessing.synonym:
                        words.append(preProcessing.synonym[prediction[0][i][0]])
                    else:
                        words.append(prediction[0][i][0])
                cv2.imwrite(raw_image_url,  cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
                current_app.logger.info('%s - %s' %('words', words))

                config_list = config_account + config_system
                detection = False
                for detect in config_list:
                    if detect in words:
                        detection = True
                        if detect in config_account:
                            scorelist = config_score['account']
                        elif detect in config_system:
                            scorelist = config_score['system']

                        # message
                        actionList = ''
                        for score in scorelist:
                            actionList = actionList + score + ', '
                        actionList = actionList[:-2]
                        response['template']['outputs'] = cardResponse(title='사진', actionList=actionList, len_score=len(scorelist))
                        response['template']['quickReplies'] = [{'action':'block', 'label':score, 'messageText':score} for score in scorelist]
                if not detection:
                    response['template']['outputs'] = cardResponse(title='사진')
            else:
                response['template']['outputs'] = cardResponse(title='사진')
        elif 'http' in message['msg'] and ('.gif' in message['msg'] or '.png' in message['msg'] or '.jpg' in message['msg'] or '.jpeg' in message['msg']):
            response['template']['outputs'] = cardResponse(title='사진')
        elif 'http' in message['msg'] and ('.mp4' in message['msg'] or '.mpg' in message['msg'] or '.avi' in message['msg']):
            response['template']['outputs'] = cardResponse(title='동영상')
        else:
            spacetext, corpus, words = preProcessing.split(message['msg'])
            current_app.logger.info('%s - %s' %('words', words))

            deepScore = deepPrediction(words)
            bayScore = bf.predict(words)

            # compare deeplearning and bayesian
            try:
                kakaoWrite(message['msg'], spacetext, corpus, words, deepScore, bayScore)
            except:
                pass

            intent = conditionalCheckIntent(words)
            if intent:
                simple, text = simpleResponse(intent=intent)
                if text == '':
                    return '', 204
                response['template']['outputs'] = text
            else:
                current_app.logger.info('%s - %s' % ('deep predcition', str(deepScore)))
                current_app.logger.info('%s - %s' %('bayesian', bayScore))
                intent = deepScore[0][0]
                if bf.category_dict[intent] > 5:
                    simple, text = simpleResponse(intent=intent)
                    if text == '':
                        return text, 204
                    if simple:
                        response['template']['outputs'] = text
                    else:
                        help = False
                        actionList = ''
                        rescore = []
                        for i, score in enumerate(deepScore):
                            if score[0] == '상담원' and i < 2:
                                help = True
                            if score[0] not in ['안녕', '연결', '수고', '감사', '문의', '진행']:
                                actionList = actionList + score[0] + ', '
                                rescore.append(score[0])
                        if help:
                            response['template']['outputs'] = cardResponse(title='상담원')
                        else:
                            actionList = actionList[:-2]
                            response['template']['outputs'] = cardResponse(title='action', actionList=actionList, len_score=len(rescore))
                            response['template']['quickReplies'] = [{'action':'block', 'label':score, 'messageText':score} for score in rescore]
                else:
                    response['template']['outputs'] = cardResponse(title='상담원')

        message['response'] = response
        userRequest[message['user']] = message
        if 'quickReplies' in response['template']:
            current_app.logger.info('%s - %s' %('response', response['template']['quickReplies']))
        else:
            current_app.logger.info('%s - %s' %('response', response['template']))
        return jsonify(response)

def deepPrediction(words):
    sentence = []
    for word in words:
        sentence.append(word_index[word])
    x = pad_sequences([sentence], maxlen=max_len)

    # https://www.tensorflow.org/api_docs/python/tf/keras/preprocessing/sequence/pad_sequences
    # tf.keras.preprocessing.sequence.pad_sequences(sequence, maxlen=2)
    # array([[0, 1], [2, 3], [5, 6]])

    y = model.predict(x)
    y = tf.nn.softmax(y).numpy().tolist()[0]

    score_list = []
    for idx in idx_label:
        score_list.append((idx_label[str(idx)], y[int(idx)]))
    score_list = sorted(score_list, key=lambda i: i[1])
    score_list.reverse()
    return score_list[0:3]

def info(kakaoJson):
    if kakaoJson:
        return {'user':kakaoJson['userRequest']['user']['id'], 'msg':kakaoJson['userRequest']['utterance'], 'type':kakaoJson['intent']['name'], 'timestamp':int(time.time())}
    else:
        current_app.logger.info('%s - %s' %('kakaoJson', kakaoJson))
        return None
