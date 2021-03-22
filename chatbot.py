import os
import logging
from flask import Flask

def create_app():
    log_dir = 'log'
    if os.path.exists(log_dir):
        pass
    else:
        os.makedirs(log_dir)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler(log_dir + '/server.log')
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(32)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)

    from views import main_views, intent_views, monitoring_views, api_views
    app.register_blueprint(main_views.bp)
    app.register_blueprint(intent_views.bp)
    app.register_blueprint(monitoring_views.bp)
    app.register_blueprint(api_views.bp)

    return app

if __name__ == '__main__' :
    app = create_app()
    app.run(host='0.0.0.0', port=8080, debug=True)