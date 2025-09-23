from flask import Flask


def create_app():
    app = Flask(__name__)

    @app.route('/')
    def hello():
        return 'Hello, Dockerized Flask with uWSGI!'

    @app.route('/health')
    def health():
        return {'status': 'healthy'}

    return app