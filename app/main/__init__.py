# -*- coding: utf-8 -*-

from flask import Blueprint

bp = Blueprint('main', __name__)

# импортируем внизу во избежание циклических импортов внутри модуля
from app.main import routes
