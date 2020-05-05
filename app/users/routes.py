# -*- coding: utf-8 -*-

from typing import Union
from werkzeug.wrappers.response import Response
from flask_login import current_user, logout_user, login_user, login_required
from flask import redirect, url_for, request, render_template, flash, Markup
from werkzeug.urls import url_parse

from app.users import bp
from app.users.forms import LoginForm, RegistrationForm
from app.model import *
from app.users.utils import send_login_password
from app.utils import admin_required


BASE_URL = "/users"


@bp.route(f"{BASE_URL}/login", methods=["GET", "POST"])
def login() -> Union[str, Response]:
    if current_user.is_authenticated:
        return redirect(url_for('main.route_page'))

    form = LoginForm()
    if form.validate_on_submit():
        user = UserCollection.find_one(form.login.data)

        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.route_page')

        return redirect(next_page)

    return render_template("users/login.html", title='Авторизация', form=form)


@bp.route(f"{BASE_URL}/logout")
@login_required
def logout() -> Response:
    logout_user()
    return redirect(url_for("users.login"))


@bp.route(f'{BASE_URL}/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register() -> Union[str, Response]:
    form = RegistrationForm()

    if form.validate_on_submit():
        user = User.register(form.name.data, form.surname.data, form.email.data)
        send_login_password(user)

        UserCollection.save_data(user)
        flash(Markup(f"Пользователь <b>{user.name} {user.surname}</b> создан в системе!"))

        return redirect(url_for('main.route_page'))

    return render_template("data_entry_form.html", title='Регистрация пользователя', form=form)


@bp.route(f"{BASE_URL}/delete/<user_id>")
@login_required
@admin_required
def delete(user_id: str) -> Response:
    UserCollection.delete_one(user_id)
    return redirect(url_for('main.route_page'))


@bp.route(f"{BASE_URL}/page/<user_id>")
@login_required
@admin_required
def route_page(user_id: str) -> str:
    user = UserCollection.find_one_or_404(user_id)
    return render_template("users/user.html", title=f"{user.name} {user.surname}", user=user)


@bp.route(f"{BASE_URL}/send_data/<user_id>")
@login_required
@admin_required
def send_data(user_id: str) -> Response:
    user = UserCollection.find_one_or_404(user_id)
    user.set_new_password()
    send_login_password(user)
    UserCollection.save_data(user)

    return redirect(url_for('users.route_page', user_id=user.id))
