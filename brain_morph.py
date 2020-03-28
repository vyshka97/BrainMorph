# -*- coding: utf-8 -*-

from app import flask_app
from app.model import PatientCollection


@flask_app.shell_context_processor
def make_shell_context():
    return {PatientCollection.__name__: PatientCollection}
