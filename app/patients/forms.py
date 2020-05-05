# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, TextAreaField, SubmitField, HiddenField
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired, NumberRange, Regexp, ValidationError, Optional
from dateutil.relativedelta import relativedelta
from datetime import datetime

from app.constants import INPUT_REQUIRED_MESSAGE, NAME_SURNAME_REGEXP, NAME_PLACEHOLDER, SURNAME_PLACEHOLDER

__all__ = ["PatientRegistrationForm", "PatientPrimaryForm", "SecondaryBiomarkerForm"]


class _CustomIntegerField(IntegerField):
    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = int(valuelist[0])
            except ValueError:
                self.data = None
                raise ValueError(self.gettext("В поле нужно вводить целое число"))


class PatientRegistrationForm(FlaskForm):
    patient_id = HiddenField(default=None)

    name = StringField("Имя", description="Введите имя пациента",
                       render_kw={"placeholder": NAME_PLACEHOLDER, "maxlength": 30},
                       validators=[
                           InputRequired(message=INPUT_REQUIRED_MESSAGE),
                           Regexp(NAME_SURNAME_REGEXP, message="Имя должно содержать только кириллицу"),
                       ])

    surname = StringField("Фамилия", description="Введите фамилию пациента",
                          render_kw={"placeholder": SURNAME_PLACEHOLDER, "maxlength": 50},
                          validators=[
                              InputRequired(message=INPUT_REQUIRED_MESSAGE),
                              Regexp(NAME_SURNAME_REGEXP, message="Фамилия должна содержать только кириллицу"),
                          ])

    birthday = DateField("Дата рождения", description="Введите дату рождения пациента",
                         validators=[InputRequired(message=INPUT_REQUIRED_MESSAGE)])

    mobile_number = StringField("Номер мобильного телефона", id="telephone", render_kw={"maxlength": 15},
                                description="Введите номер мобильного телефона пациента после +7",
                                validators=[
                                    InputRequired(message=INPUT_REQUIRED_MESSAGE),
                                    Regexp(r"^\([0-9]{3}\) [0-9]{3}-[0-9]{2}-[0-9]{2}$",
                                           message="В номере телефона должно быть 10 цифр"),
                                ])

    submit = SubmitField("Отправить")

    def validate_birthday(self, birthday: DateField) -> None:
        if birthday.data > datetime.now().date() - relativedelta(years=18):
            raise ValidationError("Возраст пациента должен быть больше 18 лет")


class PatientPrimaryForm(FlaskForm):
    patient_id = HiddenField(default=None)

    height = _CustomIntegerField("Рост (см)", description="Введите рост пациента", default=None,
                          validators=[Optional(), NumberRange(min=1, max=300, message="Рост должен быть от 1 до 300")])

    weight = _CustomIntegerField("Вес (кг)", description="Введете вес пациента", default=None,
                          validators=[Optional(), NumberRange(min=1, max=500, message="Вес должен быть от 1 до 500")])

    is_smoking = BooleanField("Курит ?", default=False)
    complaints = TextAreaField("Жалобы", description="Напишите жалобы пациента")
    submit = SubmitField("Отправить")


class SecondaryBiomarkerForm(FlaskForm):
    patient_id = HiddenField(default=None)

    mmse = _CustomIntegerField("MMSE", description="Введите результат теста MMSE",
                                validators=[Optional(),
                                            NumberRange(min=1, max=30, message="MMSE должен быть от 1 до 30")])

    moca = _CustomIntegerField("MoCA", description="Введите результат теста MoCA",
                                validators=[Optional(),
                                            NumberRange(min=1, max=30, message="MoCA должен быть от 1 до 30")])

    sumbit = SubmitField("Отправить")
