# -*- coding: utf-8 -*-

import os

from flask import Flask
from flask_pymongo import PyMongo
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from nipype import config, logging

from config import Config

pymongo = PyMongo()

bootstrap = Bootstrap()

login = LoginManager()
login.login_view = "users.login"
login.login_message = "Для получения доступа в систему пройдите авторизацию"

mail = Mail()

csrf = CSRFProtect()


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    pymongo.init_app(app)
    bootstrap.init_app(app)
    login.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.users import bp as users_bp
    app.register_blueprint(users_bp)

    from app.patients import bp as patients_bp
    app.register_blueprint(patients_bp)

    nipype_crash_dir = app.config["NIPYPE_CRASH_DIR"]
    if not os.path.isdir(nipype_crash_dir):
        os.makedirs(nipype_crash_dir, exist_ok=True)

    nipype_config_dict = {'execution': {
        'crashdump_dir': os.path.abspath(nipype_crash_dir)
    }}
    config.update_config(nipype_config_dict)
    logging.update_logging(config)

    return app


# импортируем внизу во избежание циклических импортов внутри пакета
from app import model, utils
