import requests
import csv
import datetime

def csvWrite(msg, spacetext, malist, words, deepScore, scorelist):
    f = open('compare.csv', 'a', encoding='utf-8-sig', newline='')
    wr = csv.writer(f)
    add = [datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S'), msg, spacetext, malist, words]
    for i in deepScore:
        add.append(i[0])
    for i in scorelist:
        add.append(i[0])
    wr.writerow(add)
    f.close()

def _request_data(verb, url, params=None, headers=None, data=None, stream=False):
    try:
        if data is not None:
            r = requests.request(verb, url, params=params, headers=headers, json=data, timeout=3.0)
        else:
            r = requests.request(verb, url, params=params, headers=headers, timeout=3.0)
    except Exception as e:
        print(e)
        return None
    else:
        if r.status_code == 200 or r.status_code == 201:
            return r.content
        else:
            print(r.status_code, data)
            return None