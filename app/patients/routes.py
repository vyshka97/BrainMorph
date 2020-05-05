# -*- coding: utf-8 -*-

from flask_login import login_required
from typing import Union
from werkzeug.wrappers.response import Response
from flask import request, flash, Markup, redirect, url_for, render_template, send_file
from datetime import datetime
from io import BytesIO

from app.patients import bp
from app.utils import user_required
from app.model import *
from app.patients.forms import *
from app.patients.utils import *

BASE_URL = "/patients"


@bp.route(f"{BASE_URL}/register", methods=["GET", "POST"])
@login_required
@user_required
def register() -> Union[str, Response]:
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

        patient_id = PatientCollection.save_data(data, patient_id=form.patient_id.data)

        flash(Markup("Регистрационные данные обновлены"))
        return redirect(url_for("patients.route_page", patient_id=patient_id))

    return render_template("data_entry_form.html", title="Ввод регистрационных данных", form=form)


@bp.route(f'{BASE_URL}/page/<patient_id>')
@login_required
@user_required
def route_page(patient_id: str) -> str:
    patient: Patient = PatientCollection.find_one(patient_id)
    title = f"{patient.registration_data.surname} {patient.registration_data.name}"
    return render_template("patients/patient.html", patient=patient, title=title)


@bp.route(f'{BASE_URL}/enter_primary_data', methods=["GET", "POST"])
@login_required
@user_required
def enter_primary_data() -> Union[str, Response]:
    patient_id = request.args.get("patient_id", None, type=str)
    form = PatientPrimaryForm()

    if patient_id is not None and request.method == "GET":
        data: PrimaryData = PatientCollection.find_one(patient_id, PrimaryData)

        form.patient_id.data = data.id
        form.height.data = data.height
        form.weight.data = data.weight
        form.is_smoking.data = data.is_smoking
        form.complaints.data = data.complaints

    if form.validate_on_submit():
        data = PrimaryData(height=form.height.data, weight=form.weight.data, is_smoking=form.is_smoking.data,
                           complaints=form.complaints.data)

        PatientCollection.save_data(data, patient_id=form.patient_id.data)

        flash(Markup("Первичные данные обновлены"))
        return redirect(url_for("patients.route_page", patient_id=form.patient_id.data))

    return render_template("data_entry_form.html", title="Ввод первичных данных", form=form)


@login_required
@bp.route(f'{BASE_URL}/enter_secondary_biomarkers', methods=["GET", "POST"])
@user_required
def enter_secondary_biomarkers() -> Union[str, Response]:
    patient_id = request.args.get("patient_id", None, type=str)
    form = SecondaryBiomarkerForm()

    if request.method == "GET":
        data: SecondaryBiomarkers = PatientCollection.find_one(patient_id, SecondaryBiomarkers)

        form.patient_id.data = data.id
        form.mmse.data = data.mmse
        form.moca.data = data.moca

    if form.validate_on_submit():
        data = SecondaryBiomarkers(mmse=form.mmse.data, moca=form.moca.data)
        PatientCollection.save_data(data, patient_id=form.patient_id.data)

        flash(Markup("Другие биомаркеры обновлены"))
        return redirect(url_for("patients.route_page", patient_id=form.patient_id.data))

    return render_template("data_entry_form.html", title="Ввод других биомаркеров", form=form)


@bp.route(f"{BASE_URL}/upload_series/<patient_id>", methods=["POST"])
@login_required
@user_required
def upload_series(patient_id: str) -> Response:
    save_files_from_client(patient_id)
    split_on_series(patient_id)
    return redirect(url_for("patients.route_page", patient_id=patient_id))


@bp.route(f"{BASE_URL}/series_page/<patient_id>/<series_id>")
@login_required
@user_required
def route_series_page(patient_id: str, series_id: str) -> str:
    series_data: SeriesData = PatientCollection.find_one(patient_id, SeriesData)
    series = series_data.find_or_404(series_id)
    return render_template("patients/series.html", series=series, title="Серия", patient_id=patient_id)


@bp.route(f"{BASE_URL}/delete_series/<patient_id>/<series_id>")
@login_required
@user_required
def delete_series(patient_id: str, series_id: str) -> Response:
    remove(patient_id, series_id)
    return redirect(url_for("patients.route_page", patient_id=patient_id))


@bp.route(f"{BASE_URL}/analyze_series/<patient_id>/<series_id>")
@login_required
@user_required
def analyze_series(patient_id: str, series_id: str) -> Response:
    analyze(patient_id, series_id)
    return redirect(url_for("patients.route_series_page", patient_id=patient_id, series_id=series_id))


@bp.route(f"{BASE_URL}/get_report/<patient_id>")
@login_required
@user_required
def get_report(patient_id: str) -> Union[Response]:
    patient: Patient = PatientCollection.find_one(patient_id)

    try:
        document = patient.get_report()
    except AssertionError as e:
        flash(str(e))
        return redirect(url_for("patients.route_page", patient_id=patient_id))

    f = BytesIO()
    document.save(f)
    f.seek(0)
    return send_file(f, as_attachment=True, attachment_filename='report.docx')
