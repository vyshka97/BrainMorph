# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, TextAreaField, SubmitField, HiddenField, PasswordField
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired, NumberRange, Length, Regexp, ValidationError, Email

from .model import UserCollection

INPUT_REQUIRED_VALIDATOR = InputRequired(message="Это должно быть заполнено")


class PatientRegistrationForm(FlaskForm):
    patient_id = HiddenField(default=None)

    name = StringField("Имя", description="Введите имя пациента", render_kw={"placeholder": "Иван"},
                       validators=[
                           INPUT_REQUIRED_VALIDATOR,
                           Length(min=1, max=30, message="Максимальная длина - 30 символов"),
                           Regexp(r"^[А-Яа-я \-]*$", message="Имя должно содержать только кириллицу"),
                       ])

    surname = StringField("Фамилия", description="Введите фамилию пациента", render_kw={"placeholder": "Иванов"},
                          validators=[
                              INPUT_REQUIRED_VALIDATOR,
                              Length(min=1, max=50, message="Максимальная длина - 50 символов"),
                              Regexp(r"^[А-Яа-я \-]*$", message="Фамилия должна содержать только кириллицу"),
                          ])

    birthday = DateField("Дата рождения", description="Введите дату рождения пациента",
                         validators=[INPUT_REQUIRED_VALIDATOR])

    mobile_number = StringField("Номер мобильного телефона",
                                description="Введите номер мобильного телефона пациента после +7",
                                validators=[
                                    INPUT_REQUIRED_VALIDATOR,
                                    Length(min=10, max=10, message="Номер телефона должен состоять только из 10 цифр"),
                                ])

    submit = SubmitField("Отправить")

    def validate_mobile_number(self, mobile_number: StringField) -> None:
        if not mobile_number.data.isdecimal():
            raise ValidationError("Номер телефона должен содержать только цифры")


class PatientPrimaryForm(FlaskForm):
    patient_id = HiddenField(default=None)

    height = IntegerField("Рост (см)", description="Введите рост пациента",
                          validators=[NumberRange(min=1, max=300, message="Рост должен быть от 1 до 300 включительно")])

    weight = IntegerField("Вес (кг)", description="Введете вес пациента",
                          validators=[NumberRange(min=1, max=500, message="Вес должен быть от 1 до 500 включительно")])

    is_smoking = BooleanField("Курит ?", default=False)
    complaints = TextAreaField("Жалобы", description="Напишите жалобы пациента")
    submit = SubmitField("Отправить")


class SecondaryBiomarkerForm(FlaskForm):
    patient_id = HiddenField(default=None)

    mmse = IntegerField("MMSE", description="Введите результат теста MMSE",
                        validators=[NumberRange(min=1, max=30, message="MMSE должен быть от 1 до 30 включительно")])

    moca = IntegerField("MoCA", description="Введите результат теста MoCA",
                        validators=[NumberRange(min=1, max=30, message="MoCA должен быть от 1 до 30 включительно")])

    sumbit = SubmitField("Отправить")


class LoginForm(FlaskForm):
    login = StringField("Логин", validators=[INPUT_REQUIRED_VALIDATOR],
                        description="Введите Ваш логин")

    password = PasswordField("Пароль", validators=[INPUT_REQUIRED_VALIDATOR],
                             description="Введите Ваш пароль")

    remember_me = BooleanField("Запомнить меня", default=False)
    submit = SubmitField("Войти")

    def validate(self) -> bool:
        if not super().validate():
            return False

        user = UserCollection.find_one(self.login.data)

        if user is None:
            self.login.errors.append("Неправильный логин")
            return False

        if not user.check_password(self.password.data):
            self.password.errors.append("Неправильный пароль")
            return False

        return True


class RegistrationForm(FlaskForm):
    name = StringField("Имя", description="Введите имя пользователя", render_kw={"placeholder": "Иван"},
                       validators=[
                           INPUT_REQUIRED_VALIDATOR,
                           Length(min=1, max=30, message="Максимальная длина - 30 символов"),
                           Regexp(r"^[А-Яа-я \-]*$", message="Имя должно содержать только кириллицу"),
                       ])

    surname = StringField("Фамилия", description="Введите фамилию пользователя", render_kw={"placeholder": "Иванов"},
                          validators=[
                              INPUT_REQUIRED_VALIDATOR,
                              Length(min=1, max=50, message="Максимальная длина - 50 символов"),
                              Regexp(r"^[А-Яа-я \-]*$", message="Фамилия должна содержать только кириллицу"),
                          ])

    email = StringField("Адрес электронной почты", description="Введите email пользователя",
                        render_kw={"placeholder": "email@example.com"},
                        validators=[
                            INPUT_REQUIRED_VALIDATOR,
                            Email(message="Невалидный формат email")
                        ])

    submit = SubmitField("Добавить")

    def validate_email(self, email: StringField) -> None:
        if UserCollection.has_email(email.data):
            raise ValidationError("Пользователь с таким email уже есть в системе!")

