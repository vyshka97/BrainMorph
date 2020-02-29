# -*- coding: utf-8 -*-

from flask import Flask

flask_app = Flask(__name__)

# импортируем внизу во избежание циклических импортов внутри пакета
from app import routes
