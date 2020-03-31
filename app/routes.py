# -*- coding: utf-8 -*-

from flask import render_template, redirect, url_for, flash, request, Markup
from flask_login import current_user, login_user, logout_user, login_required
from flask_pymongo import ASCENDING
from functools import partial
from enum import Enum
from datetime import datetime
from werkzeug.wrappers.response import Response
from werkzeug.urls import url_parse
from typing import Union

from app import flask_app
from .model import *
from .forms import PatientRegistrationForm, PatientPrimaryForm, SecondaryBiomarkerForm, LoginForm
from .series_utils import split_on_series, save_files_from_client, remove, analyze


class ViewPage(Enum):
    MAIN = "main.html"
    PATIENT_REGISTRATION = "patient_registration.html"
    PATIENT = "patient.html"
    PRIMARY_DATA_ENTRY = "primary_data_entry.html"
    SECONDARY_BIOMARKERS_ENTRY = "secondary_biomarkers_entry.html"
    SERIES = "series.html"
    LOGIN = "login.html"


@flask_app.route("/")
@flask_app.route("/main")
@login_required
def route_main_page() -> str:
    page_num = request.args.get('page', 1, type=int)

    sort_rules = {
        "surname": ASCENDING,
        "name": ASCENDING,
    }

    patients, has_next, has_prev = PatientCollection.paginate(page_num, RegistrationData, sort_rules=sort_rules)

    url_for_part = partial(url_for, endpoint=route_main_page.__name__)

    next_url = url_for_part(page=page_num + 1) if has_next else None
    prev_url = url_for_part(page=page_num - 1) if has_prev else None

    return render_template(ViewPage.MAIN.value, title="Главная", patients=patients, next_url=next_url,
                           prev_url=prev_url)


@flask_app.route("/patient_registration", methods=["GET", "POST"])
@login_required
def patient_registration() -> Union[str, Response]:
    patient_id = request.args.get("patient_id", None, type=str)
    form = PatientRegistrationForm()

    if patient_id is not None and request.method == "GET":
        data: RegistrationData = PatientCollection.find_one(patient_id, RegistrationData)

        form.patient_id.data = data.id
        form.name.data = data.name
        form.surname.data = data.surname
        form.birthday.data = data.birthday
        form.mobile_number.data = data.mobile_number

    elif form.validate_on_submit():
        data = RegistrationData(name=form.name.data, surname=form.surname.data, mobile_number=form.mobile_number.data,
                                birthday=datetime.combine(form.birthday.data, datetime.min.time()))

        PatientCollection.save_data(data, patient_id=form.patient_id.data)

        flash("Регистрационные данные обновлены")
        return redirect(url_for(patient_registration.__name__))

    return render_template(ViewPage.PATIENT_REGISTRATION.value, title="Ввод регистрационных данных", form=form)


@flask_app.route('/patient/<patient_id>')
@login_required
def route_patient_page(patient_id: str) -> str:
    patient = PatientCollection.find_one(patient_id)
    title = f"{patient.registration_data.surname} {patient.registration_data.name}"
    return render_template(ViewPage.PATIENT.value, patient=patient, title=title)


@flask_app.route('/patient/<patient_id>/primary_data_entry', methods=["GET", "POST"])
@login_required
def enter_primary_data(patient_id: str) -> Union[str, Response]:
    form = PatientPrimaryForm()

    if request.method == "GET":
        data: PrimaryData = PatientCollection.find_one(patient_id, PrimaryData)

        form.height.data = data.height
        form.weight.data = data.weight
        form.is_smoking.data = data.is_smoking
        form.complaints.data = data.complaints

    if form.validate_on_submit():
        data = PrimaryData(height=form.height.data, weight=form.weight.data, is_smoking=form.is_smoking.data,
                           complaints=form.complaints.data)

        PatientCollection.save_data(data, patient_id=patient_id)

        flash("Первичные данные обновлены")
        return redirect(url_for(route_patient_page.__name__, patient_id=patient_id))

    return render_template(ViewPage.PRIMARY_DATA_ENTRY.value, title="Ввод первичных данных", form=form)


@flask_app.route('/patient/<patient_id>/secondary_biomarker_entry', methods=["GET", "POST"])
@login_required
def enter_secondary_biomarkers(patient_id: str) -> Union[str, Response]:
    form = SecondaryBiomarkerForm()

    if request.method == "GET":
        data: SecondaryBiomarkers = PatientCollection.find_one(patient_id, SecondaryBiomarkers)

        form.mmse.data = data.mmse
        form.moca.data = data.moca

    if form.validate_on_submit():
        data = SecondaryBiomarkers(mmse=form.mmse.data, moca=form.moca.data)
        PatientCollection.save_data(data, patient_id=patient_id)

        flash("Другие биомаркеры обновлены")
        return redirect(url_for(route_patient_page.__name__, patient_id=patient_id))

    return render_template(ViewPage.SECONDARY_BIOMARKERS_ENTRY.value, title="Ввод других биомаркеров", form=form)


@flask_app.route("/patient/<patient_id>/upload_series", methods=["POST"])
@login_required
def upload_series(patient_id: str) -> Response:
    save_files_from_client(patient_id)
    split_on_series(patient_id)
    return redirect(url_for('route_patient_page', patient_id=patient_id))


@flask_app.route("/patient/<patient_id>/series/<series_id>")
@login_required
def route_series_page(patient_id: str, series_id: str) -> str:
    series = PatientCollection.find_one(patient_id, SeriesData).find_or_404(series_id)
    return render_template(ViewPage.SERIES.value, series=series, title="Серия", patient_id=patient_id)


@flask_app.route("/patient/<patient_id>/series/<series_id>/delete")
@login_required
def delete_series(patient_id: str, series_id: str) -> Response:
    remove(patient_id, series_id)
    return redirect(url_for(route_patient_page.__name__, patient_id=patient_id))


@flask_app.route("/patient/<patient_id>/series/<series_id>/analyze")
@login_required
def analyze_series(patient_id: str, series_id: str) -> Response:
    analyze(patient_id, series_id)
    return redirect(url_for(route_series_page.__name__, patient_id=patient_id, series_id=series_id))


@flask_app.route("/login", methods=["GET", "POST"])
def login() -> Union[str, Response]:
    if current_user.is_authenticated:
        return redirect(url_for(route_main_page.__name__))

    form = LoginForm()
    if form.validate_on_submit():
        user = UserCollection.find_one(form.login.data)

        if user is None:
            flash(Markup("Неверный логин"))
            return redirect(url_for(login.__name__))
        elif not user.check_password(form.password.data):
            flash(Markup("Неверный пароль"))
            return redirect(url_for(login.__name__))

        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for(route_main_page.__name__)

        return redirect(next_page)

    return render_template(ViewPage.LOGIN.value, title='Авторизация', form=form)


@flask_app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for(route_main_page.__name__))
