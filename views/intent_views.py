from flask import Blueprint, request, render_template
from form import IntentMessageForm
from models import get_intent_list, get_intent_paging, get_intent_data_list, post_intent

intent_list = get_intent_list()

bp = Blueprint('intent', __name__, url_prefix='/intent')

@bp.route('/')
def _list():
    page = int(request.args.get('page', 1))
    paging, data_list = get_intent_paging(intent_list, page=page)
    return render_template('intent/intent_list.html', paging=paging, data_list=data_list)

@bp.route('/<intent>/', methods=('GET', 'POST'))
def intent_detail(intent):
    form = IntentMessageForm()
    page = int(request.args.get('page', 1))
    if request.method == 'POST' and form.validate_on_submit():
        request_data = {'msg':form.msg.data, 'intent':intent}
        post_intent(request_data)
    paging, data_list = get_intent_data_list(intent, page=page)
    return render_template('intent/intent_detail.html', form=form, intent=intent, paging=paging, data_list=data_list)