from flask import Blueprint, request, render_template, url_for
from werkzeug.utils import redirect
from form import PrewordForm
from models import get_word_list, get_typo_synonym, post_pre_word
from utils import request_get

bp = Blueprint('word', __name__, url_prefix='/word')
typo_synonym = get_typo_synonym()

@bp.route('/')
def word():
    sort_type = 'count'
    page, keyword, so, so_list = request_get(request.args, sort_type=sort_type)
    paging, data_list = get_word_list(page=page, sort=so_list, keyword=keyword)
    return render_template('word/word.html', typo_synonym=typo_synonym, **locals())

@bp.route('/<word>/', methods=('GET', 'POST'))
def pre_word(word):
    form = PrewordForm()
    if request.method == 'POST' and form.validate_on_submit():
        request_data = {'type':form.type.data, 'word':word, 'sub':form.sub.data}
        post_pre_word(request_data)
        global typo_synonym
        typo_synonym = get_typo_synonym()
        return redirect(url_for('word.word'))
    return render_template('word/pre_word.html', **locals())