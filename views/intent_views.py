from flask import Blueprint, request, render_template
from form import IntentMessageForm
from models import get_intent_paging, get_intent_data_list, post_intent
from utils import request_get

bp = Blueprint('intent', __name__, url_prefix='/intent')

@bp.route('/', methods=('GET', 'POST'))
def _list():
    form = IntentMessageForm()
    sort_type = 'count'
    page, keyword, so, so_list = request_get(request.args, sort_type=sort_type)
    if request.method == 'POST' and form.validate_on_submit():
        intent = form.intent.data
        request_data = {'intent':intent}
        post_intent(request_data)
    paging, data_list, data_len = get_intent_paging(page=page, sort=so_list, keyword=keyword)
    # data_len = data_list.count()
    return render_template('intent/intent_list.html', **locals())

@bp.route('/<intent>/', methods=('GET', 'POST'))
def intent_detail(intent):
    form = IntentMessageForm()
    page, keyword, so, so_list = request_get(request.args)
    if request.method == 'POST' and form.validate_on_submit():
        request_data = {'msg':form.msg.data, 'intent':form.intent.data}
        post_intent(request_data)
    paging, data_list = get_intent_data_list(intent, page=page, keyword=keyword)
    return render_template('intent/intent_detail.html', **locals())





