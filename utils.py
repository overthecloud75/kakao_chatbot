import requests

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

def calculate_accuracy(count, today_find):
    deep_accuracy = [0, 0, 0]
    bay_accuracy = [0, 0, 0]
    unknown = 0
    no_decision = 0
    for data in today_find:
        deep = data['deep']
        bay = data['bay']
        if 'category' in data:
            category = data['category']
            if category == 'unknown':
                unknown = unknown + 1
            for i in range(3):
                if deep[i][0] == category:
                    for k in range(3):
                        if k >= i:
                            deep_accuracy[k] = deep_accuracy[k] + 1
                if bay[i][0] == category:
                    for k in range(3):
                        if k >= i:
                            bay_accuracy[k] = bay_accuracy[k] + 1
        else:
            no_decision = no_decision + 1
    for i in range(3):
        deep_accuracy[i] = int(deep_accuracy[i] / count * 100)
        bay_accuracy[i] = int(bay_accuracy[i] / count * 100)
    return count, unknown, no_decision, deep_accuracy, bay_accuracy

