from flask import Flask
import logging

def create_app():
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler('apiserver.log')
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    app = Flask(__name__)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)

    from views import api_views
    app.register_blueprint(api_views.bp)

    return app

if __name__ == '__main__' :
    app = create_app()
    app.run(host='0.0.0.0', port=8080, debug=True)