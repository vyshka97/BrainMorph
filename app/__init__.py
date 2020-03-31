# -*- coding: utf-8 -*-

from flask import Flask
from flask_pymongo import PyMongo
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from nipype import Node, Workflow
from nipype.interfaces import fsl
from werkzeug.security import generate_password_hash

from config import Config

flask_app = Flask(__name__)
flask_app.config.from_object(Config)

pymongo = PyMongo(flask_app)
patients = pymongo.db.patients
users = pymongo.db.users

bootstrap = Bootstrap(flask_app)

login = LoginManager(flask_app)

# импортируем внизу во избежание циклических импортов внутри пакета
from app import routes, model, series_utils, forms

login.login_view = routes.login.__name__

# добавляем пока одного пользователя для отладки

user = model.User(id="maks", password_hash=generate_password_hash("12345"), email="maks081197@yandex.ru")
model.UserCollection.save_data(user)
