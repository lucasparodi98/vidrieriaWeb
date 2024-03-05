import os

from flask import Flask

from flask import (
    render_template
)

from . import db
from . import auth
from . import movimiento


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY = 'dev',
        DATABASE = os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(movimiento.bp)

    # a simple page that says hello
    @app.route('/')
    def index():
        return render_template('main.html')

    app.add_url_rule('/', endpoint='index')

    return app