from flask import Blueprint, request, render_template, url_for, current_app, session, g, flash, send_file, send_from_directory
from werkzeug.utils import redirect
from form import MonitoringForm
from models import get_category_list, get_monitoring_data_list, post_monitoring, get_statistics_list
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
    page = int(request.args.get('page', 1))

    if request.method == 'POST' and form.validate_on_submit():
        category = form.category.data
        if category not in category_list and category != 'unknown':
            flash('there is no that kind of category')
        else:
            post_monitoring(timestamp=form.timestamp.data, category=category)
    paging, data_list = get_monitoring_data_list(page=page, sort='timestamp')
    return render_template('monitoring/monitoring.html', form=form, paging=paging, data_list=data_list)

@bp.route('/statistics/', methods=('GET', 'POST'))
@login_required
def statistics():
    page = int(request.args.get('page', 1))
    paging, data_list = get_statistics_list(page=page, sort='date')
    return render_template('monitoring/statistics.html', paging=paging, data_list=data_list)
