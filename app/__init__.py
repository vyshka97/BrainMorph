# -*- coding: utf-8 -*-

import os

from enum import Enum
from flask import Flask
from flask_pymongo import PyMongo
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_sendmail import Mail
from nipype import config, logging
from werkzeug.security import generate_password_hash

from config import Config


class ViewPage(Enum):
    MAIN = "main.html"
    DATA_ENTRY_FORM = "data_entry_form.html"
    PATIENT = "patient.html"
    SERIES = "series.html"
    LOGIN = "login.html"
    EMAIL = "email/login_password.html"
    ERROR_404 = "error/404.html"
    ERROR_500 = "error/500.html"


flask_app = Flask(__name__)
flask_app.config.from_object(Config)

pymongo = PyMongo(flask_app)
patients = pymongo.db.patients
users = pymongo.db.users

bootstrap = Bootstrap(flask_app)

login = LoginManager(flask_app)

mail = Mail(flask_app)

nipype_crash_dir = flask_app.config["NIPYPE_CRASH_DIR"]
if not os.path.isdir(nipype_crash_dir):
    os.makedirs(nipype_crash_dir, exist_ok=True)

nipype_config_dict = {'execution': {
    'crashdump_dir': os.path.abspath(nipype_crash_dir)
}}
config.update_config(nipype_config_dict)
logging.update_logging(config)

# импортируем внизу во избежание циклических импортов внутри пакета
from app import routes, model, series_utils, forms, errors, email_utils

login.login_view = routes.login.__name__
login.login_message = "Для получения доступа в систему пройдите авторизацию"

# добавляем администратора
admin_email = "maks@yandex.ru"
login, _ = model.User.generate_login_password(admin_email)
user = model.User(id=login, password_hash=generate_password_hash("12345"), email=admin_email,
                  name="Максим", surname="Вышегородцев", is_admin=True)
model.UserCollection.save_data(user)

# создаем индекс в коллекции пользователей
if "email_" not in users.index_information():
    users.create_index("email", name="email_", unique=True)
