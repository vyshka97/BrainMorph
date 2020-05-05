# -*- coding: utf-8 -*-

from app import create_app
from app.model import *

# создаем приложение flask
flask_app = create_app()

UserCollection.init(flask_app)


@flask_app.shell_context_processor
def make_shell_context():
    classes = [PatientCollection, Patient, RegistrationData, PrimaryData, SecondaryBiomarkers, SeriesData, Series,
               UserCollection, User]
    return {cls.__name__ : cls for cls in classes}
