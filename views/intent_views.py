from flask import Blueprint, request, render_template
from werkzeug.utils import redirect
# from flask_paginate import Pagination, get_page_args
from form import IntentMessageForm
from .config import page_default
from .utils import paginate

# database
from mongonator import Paginate, ASCENDING
from pymongo import MongoClient
mongoClient = MongoClient('mongodb://localhost:27017/')
db = mongoClient['chatbot']
collection = db['bayesian']
data = collection.find_one(filter={'category_dict': {'$exists': 'true'}})
category_dict = data['category_dict']
intent_list = []
for key in category_dict:
    intent = {'intent': key, 'count': category_dict[key]}
    intent_list.append(intent)

bp = Blueprint('intent', __name__, url_prefix='/intent')

@bp.route('/')
def _list():
    page = int(request.args.get('page', 1))
    limit = page_default['limit']
    offset = (page - 1) * limit
    count = len(intent_list)
    paging = paginate(page, limit, count)
    data_list = intent_list[offset:offset+limit]
    return render_template('intent/intent_list.html', paging=paging, data_list=data_list)

@bp.route('/<intent>/', methods=('GET', 'POST'))
def intent_detail(intent):
    form = IntentMessageForm()

    page = int(request.args.get('page', 1))
    limit = page_default['limit']
    offset = (page - 1) * limit

    collection = db['intent']
    if request.method == 'POST' and form.validate_on_submit():
        request_data = {'msg':form.msg.data, 'intent':intent}
        collection.update_one(request_data, {'$set':request_data}, upsert=True)
    data_list = collection.find(
        filter={'intent':intent}
    )
    count = data_list.count()
    data_list = data_list.limit(limit).skip(offset)
    paging = paginate(page, limit, count)
    return render_template('intent/intent_detail.html', form=form, intent=intent, paging=paging, data_list=data_list)