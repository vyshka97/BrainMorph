# -*- coding: utf-8 -*-

from app import create_app
from app.model import *

# создаем приложение flask
flask_app = create_app()

UserCollection.init(flask_app)
