# -*- coding: utf-8 -*-

from flask import Blueprint

bp = Blueprint('errors', __name__)

# импортируем внизу во избежание циклических импортов внутри модуля
from app.errors import handlers
