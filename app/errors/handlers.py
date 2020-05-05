# -*- coding: utf-8 -*-

from flask import render_template
from typing import Tuple

from app.errors import bp


@bp.app_errorhandler(404)
def not_found_error(_) -> Tuple[str, int]:
    return render_template("errors/404.html"), 404


@bp.app_errorhandler(500)
def internal_error(_) -> Tuple[str, int]:
    return render_template("errors/500.html"), 500
