# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, TextAreaField, SubmitField, HiddenField, PasswordField
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired, NumberRange, Length, Regexp, ValidationError


class PatientRegistrationForm(FlaskForm):
    patient_id = HiddenField(default=None)

    name = StringField("Имя", description="Введите имя пациента", render_kw={"placeholder": "Иван"},
                       validators=[
                           InputRequired(message="Имя должно быть заполнено"),
                           Length(min=1, max=30, message="Максимальная длина имени - 30 символов"),
                           Regexp(r"^[А-Яа-я \-]*$", message="Имя должно содержать только кириллицу"),
                       ])

    surname = StringField("Фамилия", description="Введите фамилию пациента", render_kw={"placeholder": "Иванов"},
                          validators=[
                              InputRequired(message="Фамилия должна быть заполнена"),
                              Length(min=1, max=50, message="Максимальная длина фамилии - 50 символов"),
                              Regexp(r"^[А-Яа-я \-]*$", message="Фамилия должна содержать только кириллицу"),
                          ])

    birthday = DateField("Дата рождения", description="Введите дату рождения пациента",
                         validators=[InputRequired(message="Дата рождения должна быть заполнена")])

    mobile_number = StringField("Номер мобильного телефона",
                                description="Введите номер мобильного телефона пациента после +7",
                                validators=[
                                    InputRequired(message="Номер должен быть заполнен"),
                                    Length(min=10, max=10, message="Номер телефона должен состоять только из 10 цифр"),
                                ])

    submit = SubmitField("Отправить")

    def validate_mobile_number(self, mobile_number: StringField) -> None:
        if not mobile_number.data.isdecimal():
            raise ValidationError("Номер телефона должен содержать только цифры")


class PatientPrimaryForm(FlaskForm):
    height = IntegerField("Рост (см)", description="Введите рост пациента",
                          validators=[NumberRange(min=1, max=300, message="Рост должен быть от 1 до 300 включительно")])

    weight = IntegerField("Вес (кг)", description="Введете вес пациента",
                          validators=[NumberRange(min=1, max=500, message="Вес должен быть от 1 до 500 включительно")])

    is_smoking = BooleanField("Курит ?", default=False)
    complaints = TextAreaField("Жалобы", description="Напишите жалобы пациента")
    submit = SubmitField("Отправить")


class SecondaryBiomarkerForm(FlaskForm):
    mmse = IntegerField("MMSE", description="Введите результат теста MMSE",
                        validators=[NumberRange(min=1, max=30, message="MMSE должен быть от 1 до 30 включительно")])

    moca = IntegerField("MoCA", description="Введите результат теста MoCA",
                        validators=[NumberRange(min=1, max=30, message="MoCA должен быть от 1 до 30 включительно")])

    sumbit = SubmitField("Отправить")


class LoginForm(FlaskForm):
    login = StringField("Логин", validators=[InputRequired(message="Логин обязательно должен быть введен")],
                        description="Введите Ваш логин")

    password = PasswordField("Пароль", validators=[InputRequired(message="Пароль обязательно должен быть введен")],
                             description="Введите Ваш пароль")

    remember_me = BooleanField("Запомнить меня", default=False)
    submit = SubmitField("Войти")

