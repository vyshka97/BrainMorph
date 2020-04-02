# -*- coding: utf-8 -*-

from flask import render_template
from typing import Tuple

from app import flask_app, ViewPage


@flask_app.errorhandler(404)
def not_found_error(error) -> Tuple[str, int]:
    return render_template(ViewPage.ERROR_404.value), 404


@flask_app.errorhandler(500)
def internal_error(error) -> Tuple[str, int]:
    return render_template(ViewPage.ERROR_500.value), 500
