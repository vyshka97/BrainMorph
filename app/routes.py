# -*- coding: utf-8 -*-

from flask import render_template, redirect, url_for, flash, request
from functools import partial
from enum import Enum
from datetime import datetime

from app import flask_app
from .model import PatientCollection
from .forms import PatientRegistrationForm, PatientPrimaryForm, SecondaryBiomarkerForm
from .series_utils import split_on_series, save_files_from_client, remove
from .model import RegistrationData, PrimaryData, SecondaryBiomarkers, Patient, SeriesData


class ViewPage(Enum):
    MAIN = "main.html"
    PATIENT_REGISTRATION = "patient_registration.html"
    PATIENT = "patient.html"
    PRIMARY_DATA_ENTRY = "primary_data_entry.html"
    SECONDARY_BIOMARKERS_ENTRY = "secondary_biomarkers_entry.html"
    SERIES = "series.html"


@flask_app.route("/")
@flask_app.route("/main")
def route_main_page():
    page_num = request.args.get('page', 1, type=int)

    patients = PatientCollection.get_registration_data_page(page_num)

    url_for_part = partial(url_for, endpoint=route_main_page.__name__)

    next_url = url_for_part(page=page_num + 1) if PatientCollection.has_next_page(page_num) else None
    prev_url = url_for_part(page=page_num - 1) if PatientCollection.has_prev_page(page_num) else None

    return render_template(ViewPage.MAIN.value, title="Главная", patients=patients, next_url=next_url,
                           prev_url=prev_url)


@flask_app.route("/patient_registration", methods=["GET", "POST"])
def patient_registration():
    patient_id = request.args.get("patient_id", None, type=str)
    form = PatientRegistrationForm()

    if patient_id is not None and request.method == "GET":
        data = PatientCollection.find_one(patient_id, RegistrationData)

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
def route_patient_page(patient_id: str):
    patient = PatientCollection.find_one(patient_id, Patient)
    title = f"{patient.registration_data.surname} {patient.registration_data.name}"

    return render_template(ViewPage.PATIENT.value, patient=patient, title=title)


@flask_app.route('/patient/<patient_id>/primary_data_entry', methods=["GET", "POST"])
def enter_primary_data(patient_id: str):
    form = PatientPrimaryForm()

    if request.method == "GET":
        data = PatientCollection.find_one(patient_id, PrimaryData)

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
def enter_secondary_biomarkers(patient_id: str):
    form = SecondaryBiomarkerForm()

    if request.method == "GET":
        data = PatientCollection.find_one(patient_id, SecondaryBiomarkers)

        form.mmse.data = data.mmse
        form.moca.data = data.moca

    if form.validate_on_submit():
        data = SecondaryBiomarkers(mmse=form.mmse.data, moca=form.moca.data)
        PatientCollection.save_data(data, patient_id=patient_id)

        flash("Другие биомаркеры обновлены")
        return redirect(url_for(route_patient_page.__name__, patient_id=patient_id))

    return render_template(ViewPage.SECONDARY_BIOMARKERS_ENTRY.value, title="Ввод других биомаркеров", form=form)


@flask_app.route("/patient/<patient_id>/upload_series", methods=["POST"])
def upload_series(patient_id: str):
    save_files_from_client(patient_id)
    split_on_series(patient_id)
    return redirect(url_for('route_patient_page', patient_id=patient_id))


@flask_app.route("/patient/<patient_id>/series/<series_id>")
def route_series_page(patient_id: str, series_id: str):
    series = PatientCollection.find_one(patient_id, SeriesData).find_or_404(series_id)
    return render_template(ViewPage.SERIES.value, series=series, title="Серия", patient_id=patient_id)


@flask_app.route("/patient/<patient_id>/series/<series_id>/delete")
def delete_series(patient_id: str, series_id: str):
    remove(patient_id, series_id)
    return redirect(url_for(route_patient_page.__name__, patient_id=patient_id))


@flask_app.route("/patient/<patient_id>/series/<series_id>/analyze")
def analyze_series(patient_id: str, series_id: str):
    analyze(patient_id, series_id)
    return redirect(url_for(route_series_page.__name__, patient_id=patient_id, series_id=series_id))
