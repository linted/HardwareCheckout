from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
import json

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()


def create_app():
    """

    :return:
    """
    app = Flask(__name__)

    terminal_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config', 'terminals.json')
    terminals = []
    with open(terminal_file_path, 'r') as fh:
        terminals = json.loads(fh.read())

    app.config['SECRET_KEY'] = '9OLWxND4o83j4K4iuopO'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    app.config['TERMINALS'] = terminals

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        """

        :param user_id:
        :return:
        """
        return User.query.get(int(user_id))

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app



