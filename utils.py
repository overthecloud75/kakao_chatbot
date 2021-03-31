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

def paginate(page, per_page, count):
    offset = (page - 1) * per_page
    total_pages = int(count / per_page) + 1
    screen_pages = 10

    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    start_page = (page - 1) // screen_pages * screen_pages + 1

    pages = []
    prev_num = start_page - screen_pages
    next_num = start_page + screen_pages

    if start_page - screen_pages > 0:
        has_prev = True
    else:
        has_prev = False
    if start_page + screen_pages > total_pages:
        has_next = False
    else:
        has_next = True
    if total_pages > screen_pages + start_page:
        for i in range(screen_pages):
            pages.append(i + start_page)
    elif total_pages < screen_pages:
        for i in range(total_pages):
            pages.append(i + start_page)
    else:
        for i in range(total_pages - start_page + 1):
            pages.append(i + start_page)
    paging = {'page':page,
              'has_prev':has_prev,
              'has_next':has_next,
              'prev_num':prev_num,
              'next_num':next_num,
              'count':count,
              'offset':offset,
              'pages':pages,
              'screen_pages':screen_pages,
              'total_pages':total_pages
              }
    return paging

def calculate_accuracy(count, today_find):
    deep_accuracy = [0, 0, 0]
    bay_accuracy = [0, 0, 0]
    unknown = 0
    no_decision = 0
    no_bay = 0
    for data in today_find:
        deep = data['deep']
        bay = data['bay']
        if 'category' in data:
            category = data['category']
            if category == 'unknown':
                unknown = unknown + 1
            if not bay:
                no_bay = no_bay + 1
            for i in range(3):
                if deep[i][0] == category:
                    for k in range(3):
                        if k >= i:
                            deep_accuracy[k] = deep_accuracy[k] + 1
                if bay:
                    if bay[i][0] == category:
                        for k in range(3):
                            if k >= i:
                                bay_accuracy[k] = bay_accuracy[k] + 1
        else:
            no_decision = no_decision + 1
    if count - no_decision:
        for i in range(3):
            deep_accuracy[i] = int(deep_accuracy[i] / (count - no_decision) * 100)
            bay_accuracy[i] = int(bay_accuracy[i] / (count - no_decision - no_bay) * 100)
    return count, unknown, no_decision, deep_accuracy, bay_accuracy

def request_get(request_data, sort_type='timestamp'):
    page = int(request_data.get('page', 1))
    keyword = request_data.get('kw', None)
    if keyword == '?':
        keyword = '\?'
    # pymongo.errors.OperationFailure: Regular expression is invalid
    # https://stackoverflow.com/questions/43171401/invalid-regular-expression-nothing-to-repeat-error
    so = request_data.get('so', 'recent')
    so_list= [(sort_type, -1)]
    if so=='old' or so=='unpopular':
        so_list = [(sort_type, 1)]
    return page, keyword, so, so_list