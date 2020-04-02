# -*- coding: utf-8 -*-

from enum import Enum
from flask import Flask
from flask_pymongo import PyMongo
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_sendmail import Mail
from nipype import Node, Workflow
from nipype.interfaces import fsl
from werkzeug.security import generate_password_hash

from config import Config


class ViewPage(Enum):
    MAIN = "main.html"
    PATIENT_REGISTRATION = "patient_registration.html"
    PATIENT = "patient.html"
    PRIMARY_DATA_ENTRY = "primary_data_entry.html"
    SECONDARY_BIOMARKERS_ENTRY = "secondary_biomarkers_entry.html"
    SERIES = "series.html"
    LOGIN = "login.html"
    USER_REGISTRATION = "user_registration.html"
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
