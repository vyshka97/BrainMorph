# -*- coding: utf-8 -*-

from app import flask_app
from app.model import *


@flask_app.shell_context_processor
def make_shell_context():
    classes = [PatientCollection, Patient, RegistrationData, PrimaryData, SecondaryBiomarkers, SeriesData, Series,
               UserCollection, User]
    return {cls.__name__ : cls for cls in classes}
