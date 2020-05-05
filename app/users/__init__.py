# -*- coding: utf-8 -*-

from flask import Blueprint

bp = Blueprint('users', __name__)

# импортируем внизу во избежание циклических импортов внутри модуля
from app.users import routes, utils
