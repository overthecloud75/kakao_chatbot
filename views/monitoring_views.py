from flask import Blueprint, request, render_template, url_for, g, flash
from werkzeug.utils import redirect
from form import MonitoringForm
from models import get_category_list, get_monitoring_data_list, post_monitoring, get_nlp_list, get_nlp_wrong_list, get_accuracy_list, get_statistics_list
from utils import request_get
import functools

category_list = get_category_list()

# blueprint
bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('main.login'))
        return view(**kwargs)
    return wrapped_view

@bp.route('/', methods=('GET', 'POST'))
def monitoring():
    form = MonitoringForm()
    sort_type = 'timestamp'
    page, keyword, so, so_list = request_get(request.args, sort_type=sort_type)
    if request.method == 'POST' and form.validate_on_submit():
        category = form.category.data
        if category not in category_list and category != 'unknown':
            flash('there is no that kind of category')
        else:
            post_monitoring(timestamp=form.timestamp.data, category=category)
    paging, data_list = get_monitoring_data_list(page=page, sort=so_list, keyword=keyword)
    return render_template('monitoring/monitoring.html', **locals())

@bp.route('/nlp/')
def nlp():
    page, keyword, so, so_list = request_get(request.args)
    paging, data_list = get_nlp_list(page=page, keyword=keyword)
    return render_template('monitoring/nlp.html', **locals())

@bp.route('/wrong_prediction/')
def wrong_prediction():
    page, keyword, so, so_list = request_get(request.args)
    paging, data_list = get_nlp_wrong_list(page=page, keyword=keyword)
    return render_template('monitoring/wrong_prediction.html', **locals())

@bp.route('/accuracy/')
@login_required
def accuracy():
    sort_type = 'date'
    page, keyword, so, so_list = request_get(request.args, sort_type=sort_type)
    paging, collection_list = get_accuracy_list(page=page, sort=so_list)
    data_list = []
    xlabels = []
    deep_dataset1 = []
    deep_dataset2 = []
    deep_dataset3 = []
    bay_dataset1 = []
    bay_dataset2 = []
    bay_dataset3 = []
    for data in collection_list:
        data_list.append(data)
        xlabels.append(data['date'])
        deep_dataset1.append(data['deep_accuracy'][0])
        deep_dataset2.append(data['deep_accuracy'][1])
        deep_dataset3.append(data['deep_accuracy'][2])
        bay_dataset1.append(data['bay_accuracy'][0])
        bay_dataset2.append(data['bay_accuracy'][1])
        bay_dataset3.append(data['bay_accuracy'][2])
    xlabels.reverse()
    deep_dataset1.reverse()
    deep_dataset2.reverse()
    deep_dataset3.reverse()
    bay_dataset1.reverse()
    bay_dataset2.reverse()
    bay_dataset3.reverse()

    sort_type = 'timestamp'
    return render_template('monitoring/accuracy.html', **locals())

@bp.route('/statistics/')
@login_required
def statistics():
    sort_type = 'date'
    page, keyword, so, so_list = request_get(request.args, sort_type=sort_type)
    accuracy_list, word_list = get_statistics_list()
    xlabels = []
    deep_dataset1 = []
    deep_dataset2 = []
    deep_dataset3 = []
    bay_dataset1 = []
    bay_dataset2 = []
    bay_dataset3 = []
    for data in accuracy_list:
        xlabels.append(data['date'])
        deep_dataset1.append(data['deep_accuracy'][0])
        deep_dataset2.append(data['deep_accuracy'][1])
        deep_dataset3.append(data['deep_accuracy'][2])
        bay_dataset1.append(data['bay_accuracy'][0])
        bay_dataset2.append(data['bay_accuracy'][1])
        bay_dataset3.append(data['bay_accuracy'][2])

    word_set = []
    count_set = []
    for data in word_list:
        word_set.append(data['word'])
        count_set.append(data['count'])
    return render_template('monitoring/statistics.html', **locals())

# render_template with multiple variables
# **locals() : https://stackoverflow.com/questions/12096522/render-template-with-multiple-variables