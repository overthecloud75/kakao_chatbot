from flask import Blueprint, request, render_template
from werkzeug.utils import redirect
from form import IntentMessageForm

# database
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
    return render_template('intent/intent_list.html', intent_list=intent_list)

@bp.route('/<intent>/', methods=('GET', 'POST'))
def intent_detail(intent):
    form = IntentMessageForm()
    collection = db['intent']
    if request.method == 'POST' and form.validate_on_submit():
        request_data = {'msg':form.msg.data, 'intent':intent}
        collection.update_one(request_data, {'$set':request_data}, upsert=True)
    intent_list = collection.find(
        filter={'intent':intent}
    )
    return render_template('intent/intent_detail.html', form=form, intent=intent, intent_list=intent_list)