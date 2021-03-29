from flask import Blueprint, request, render_template, url_for, g, flash
from werkzeug.utils import redirect
from form import MonitoringForm
from models import get_category_list, get_monitoring_data_list, post_monitoring, get_nlp_list, get_statistics_list
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

@bp.route('/statistics/', methods=('GET', 'POST'))
@login_required
def statistics():
    sort_type = 'date'
    page, keyword, so, so_list = request_get(request.args, sort_type=sort_type)
    paging, collection_list = get_statistics_list(page=page, sort=so_list)
    data_list = []
    xlabels = []
    deep_dataset = []
    bay_dataset = []
    for data in collection_list:
        data_list.append(data)
        xlabels.append(data['date'])
        deep_dataset.append(data['deep_accuracy'][0])
        bay_dataset.append(data['bay_accuracy'][0])
    xlabels.reverse()
    deep_dataset.reverse()
    bay_dataset.reverse()
    sort_type = 'timestamp'
    return render_template('monitoring/statistics.html', **locals())

# render_template with multiple variables
# **locals() : https://stackoverflow.com/questions/12096522/render-template-with-multiple-variables