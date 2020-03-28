# -*- coding: utf-8 -*-

from flask import Flask
from config import Config
from flask_pymongo import PyMongo
from flask_bootstrap import Bootstrap

flask_app = Flask(__name__)
flask_app.config.from_object(Config)

patients = PyMongo(flask_app).db.patients

bootstrap = Bootstrap(flask_app)

# импортируем внизу во избежание циклических импортов внутри пакета
from app import routes
