# -*- coding: utf-8 -*-

from flask_login import login_required, current_user
from flask import request, render_template, url_for
from flask_pymongo import ASCENDING
from functools import partial

from app.main import bp
from app.model import *


BASE_URL = "/main"


@bp.route("/")
@bp.route(BASE_URL)
@login_required
def route_page() -> str:
    if current_user.is_admin:
        users = UserCollection.find_all()
        return render_template("main.html", title="Главная", users=users)

    page_num = request.args.get('page', 1, type=int)

    sort_rules = {
        f"{RegistrationData.FIELD_NAME}.surname": ASCENDING,
        f"{RegistrationData.FIELD_NAME}.name": ASCENDING,
    }

    patients, has_next, has_prev = PatientCollection.paginate(page_num, sort_rules=sort_rules)

    url_for_part = partial(url_for, endpoint="main.route_page")

    next_url = url_for_part(page=page_num + 1) if has_next else None
    prev_url = url_for_part(page=page_num - 1) if has_prev else None

    return render_template("main.html", title="Главная", patients=patients, next_url=next_url,
                           prev_url=prev_url)
