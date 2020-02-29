# -*- coding: utf-8 -*-

from flask import Flask

app = Flask(__name__)

# импортируем внизу во избежание циклических импортов внутри пакета
from app import routes
