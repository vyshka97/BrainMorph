# -*- coding: utf-8 -*-

from flask import Blueprint

bp = Blueprint('patients', __name__)

# импортируем внизу во избежание циклических импортов внутри модуля
from app.patients import routes