from flask import Blueprint, request, render_template, url_for, current_app, session, g, flash, send_file, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import redirect
import functools
from datetime import datetime

from form import UserCreateForm, UserLoginForm

# database
from pymongo import MongoClient
mongoClient = MongoClient('mongodb://localhost:27017/')
db = mongoClient['chatbot']

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('main.login'))
        return view(**kwargs)
    return wrapped_view

# blueprint
bp = Blueprint('main', __name__, url_prefix='/')

@bp.route('/')
def index():
    return render_template('/base.html')

@bp.route('/signup/', methods=('GET', 'POST'))
def signup():
    form = UserCreateForm()
    if request.method == 'POST' and form.validate_on_submit():
        request_data = {'group': form.group.data,  'name': form.name.data, 'email': form.email.data, 'password': generate_password_hash(form.password1.data)}
        collection = db['users']
        user_data = collection.find_one(filter={'email': request_data['email']})
        if user_data:
            flash('이미 존재하는 사용자입니다.')
        else:
            user_data = collection.find_one(filter={'group': request_data['group']})
            request_data['admin'] = False
            if user_data is None:
                request_data['admin'] = True
            user_data = collection.find_one(sort=[('create_time', -1)])
            if user_data:
                user_id = user_data['user_id'] + 1
            else:
                user_id = 1
            request_data['create_time'] = str(datetime.now())
            request_data['user_id'] = user_id
            collection.insert(request_data)
            return redirect(url_for('main.index'))
    return render_template('/signup.html', form=form)

@bp.route('/login/', methods=('GET', 'POST'))
def login():
    form = UserLoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        error = None
        request_data = {'email': form.email.data, 'password': form.password.data}
        collection = db['users']
        user_data = collection.find_one(filter={'email': request_data['email']})
        if not user_data:
            error = "존재하지 않는 사용자입니다."
        elif not check_password_hash(user_data['password'], request_data['password']):
            error = "비밀번호가 올바르지 않습니다."
        if error is None:
            del user_data['_id']
            del user_data['password']

            session.clear()
            for key in user_data:
                session[key] = user_data[key]
            return redirect(url_for('main.index'))
        flash(error)
    return render_template('/login.html', form=form)

@bp.route('/logout/')
@login_required
def logout():
    session.clear()
    return redirect(url_for('main.index'))

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = {}
        for key in session:
            g.user[key] = session[key]


