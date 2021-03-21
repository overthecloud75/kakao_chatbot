from flask import Blueprint, request, render_template, url_for, current_app, session, g, flash, send_file, send_from_directory
from werkzeug.utils import redirect
from form import MonitoringForm

# database
from pymongo import MongoClient
mongoClient = MongoClient('mongodb://localhost:27017/')
db = mongoClient['chatbot']

collection = db['bayesian']
data = collection.find_one(filter={'category_dict': {'$exists': 'true'}})
category_dict = data['category_dict']
category_list = []
for key in category_dict:
    category_list.append(key)
# blueprint
bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')

@bp.route('/', methods=('GET', 'POST'))
def monitoring():
    form = MonitoringForm()
    collection = db['kakao']
    if request.method == 'POST' and form.validate_on_submit():
        category = form.category.data
        if category not in category_list:
            flash('there is no that kind of label')
        else:
            collection.update_one({'timestamp': form.timestamp.data}, {'$set': {'category': category}})
    data_list = collection.find(sort=[('timestamp', -1)])
    return render_template('monitoring/monitoring.html', form=form, data_list=data_list)

@bp.route('/statistics/', methods=('GET', 'POST'))
def statistics():
    return redirect(url_for('main.index'))