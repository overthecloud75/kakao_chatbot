def conditionalCheckIntent(words):
    intent = None
    if len(words) == 0:
        intent = '연결'
    elif len(words) == 1 and ('맞다' in words or '그렇다' in words or '없다' in words or '해결' in words or '되다' in words or '가능' in words or '종료' in words or '사용' in words):
        intent = '연결'
    elif len(words) <= 2 and ('알다' in words or '없다' in words or '완료' in words or '해보다' in words or '죄송' in words):
        intent = '연결'
    elif len(words) <= 2 and '안녕' in words[0]:
        intent = '안녕'
    elif len(words) == 1 and '어떻다' in words:
        intent = '문의'
    elif len(words) == 1 and '이상' in words:
        intent = '문의'
    elif len(words) <= 3 and ('되어다' in words or '돼다' in words) and (
            '정지' not in words and '건가' not in words and '안' not in words and '변경' not in words):
        intent = '수고'
    elif len(words) <= 4 and ('찾다' in words or '성공' in words):
        intent = '수고'
    elif len(words) <= 4 and ('정상' in words and '동작' in words):
        intent = '수고'
    elif len(words) <= 2 and ('로그인' in words and '되다' in words and '안' not in words):
        intent = '수고'
    elif len(words) <= 4 and ('감사' in words and '알다' in words) and (
            '방법' not in words and '안' not in words and '않다' not in words):
        intent = '수고'
    elif len(words) <= 2 and ('그렇게' in words and '해주다' in words):
        intent = '진행'
    elif len(words) <= 4 and '수고' in words and '안' not in words:
        intent = '감사'
    return intent

def simpleResponse(intent=None):
    simple = True
    if intent == '안녕':
        text = [{'simpleText':{'text':'안녕하세요.'}}]
    elif intent == '수고':
        text = [{'simpleText':{'text':'수고하셨습니다.'}}]
    elif intent == '감사':
        text = [{'simpleText':{'text':'감사합니다.'}}]
    elif intent == '문의':
        text = [{'simpleText':{'text':'어떤 문의일까요?'}}]
    elif intent == '진행':
        text = [{'simpleText':{'text':'네 알겠습니다.'}}]
    elif intent == '연결':
        text = ''
    else:
        simple =False
        text = None
    return simple, text

def cardResponse(title='상담원', actionList=None, len_score=None):
    if title == '상담원':
        card = [{'basicCard':{'title':title,
                              'description':'"상담원 연결"을 누른 후 얘기 부탁 드립니다.',
                              'buttons':[{'action':'operator', 'label':'상담원 연결'}]}}]
    elif title == '챗봇':
        card = [{'basicCard':{'title':title + ' 사용법에 익숙치 않은가 봐요?',
                              'description':'"챗봇 사용법"을 누른 후 얘기 부탁 드립니다.',
                              'buttons':[{'action':'block', 'label':'챗봇 사용법'}]}}]
    elif title=='사진' or title=='동영상':
        if actionList:
            card = [{'basicCard':{'title':'아래 말풍선(' + actionList + ')중 하나를 선택해 주세요.',
                                  'description':'사진으로부터 ' + str(len_score) + '가지 의도를 뽑았습니다.'}}]
        else:
            card = [{'basicCard':{'title':title + '을 보내셨나 봐요?',
                                  'description':'"상담원 연결"을 누른 후 현상에 대한 설명 추가 부탁 드립니다.',
                                  'buttons':[{'action':'operator', 'label':'상담원 연결'}]}}]
    elif title=='action':
        card = [{'basicCard':{'title':'아래 말풍선(' + actionList + ')중 하나를 선택해 주세요.',
                              'description':'질문으로부터 가능성 높은 ' + str(len_score) + '가지 의도를 뽑았습니다.'}}]
    else:
        card = None
    return card