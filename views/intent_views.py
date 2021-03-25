from flask import Blueprint, request, render_template
from form import IntentMessageForm
from models import get_intent_list, get_intent_paging, get_intent_data_list, post_intent, get_nlp_list, get_word_list
from utils import request_get

intent_list = get_intent_list()

bp = Blueprint('intent', __name__, url_prefix='/intent')

@bp.route('/', methods=('GET', 'POST'))
def _list():
    form = IntentMessageForm()
    # sort_type = 'count'
    page, keyword, so, so_list = request_get(request.args) #, sort_type=sort_type)
    page = int(request.args.get('page', 1))
    if request.method == 'POST' and form.validate_on_submit():
        intent = form.msg.data
        request_data = {'intent':intent}
        post_intent(request_data)
        global intent_list
        intent_list = get_intent_list()
    paging, data_list = get_intent_paging(intent_list, page=page, sort=so_list)
    return render_template('intent/intent_list.html', **locals())

@bp.route('/<intent>/', methods=('GET', 'POST'))
def intent_detail(intent):
    form = IntentMessageForm()
    page = int(request.args.get('page', 1))
    if request.method == 'POST' and form.validate_on_submit():
        request_data = {'msg':form.msg.data, 'intent':intent}
        post_intent(request_data)
    paging, data_list = get_intent_data_list(intent, page=page)
    return render_template('intent/intent_detail.html', **locals())

@bp.route('/nlp/')
def nlp():
    page, keyword, so, so_list = request_get(request.args)
    paging, data_list = get_nlp_list(page=page, keyword=keyword)
    return render_template('intent/nlp.html', **locals())

@bp.route('/word/')
def word():
    sort_type = 'count'
    page, keyword, so, so_list = request_get(request.args, sort_type=sort_type)
    print(so, so_list)
    paging, data_list = get_word_list(page=page, sort=so_list)
    return render_template('intent/word.html', **locals())