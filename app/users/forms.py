# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, PasswordField
from wtforms.validators import InputRequired, Length, Regexp, ValidationError, Email

from app.model import UserCollection
from app.constants import INPUT_REQUIRED_MESSAGE, NAME_SURNAME_REGEXP, NAME_PLACEHOLDER, SURNAME_PLACEHOLDER


class LoginForm(FlaskForm):
    login = StringField("Логин", validators=[InputRequired(message=INPUT_REQUIRED_MESSAGE)],
                        description="Введите Ваш логин")

    password = PasswordField("Пароль", validators=[InputRequired(message=INPUT_REQUIRED_MESSAGE)],
                             description="Введите Ваш пароль")

    remember_me = BooleanField("Запомнить меня", default=False)
    submit = SubmitField("Войти")

    def validate(self) -> bool:
        if not super().validate():
            return False

        user = UserCollection.find_one(self.login.data)

        if user is None:
            self.login.errors.append("Пользователя с таким логином не существует")
            return False

        if not user.check_password(self.password.data):
            self.password.errors.append("Неправильный пароль")
            return False

        return True


class RegistrationForm(FlaskForm):
    name = StringField("Имя", description="Введите имя пользователя",
                       render_kw={"placeholder": NAME_PLACEHOLDER, "maxlength": 30},
                       validators=[
                           InputRequired(message=INPUT_REQUIRED_MESSAGE),
                           Regexp(NAME_SURNAME_REGEXP, message="Имя должно содержать только кириллицу"),
                       ])

    surname = StringField("Фамилия", description="Введите фамилию пользователя",
                          render_kw={"placeholder": SURNAME_PLACEHOLDER, "maxlength": 50},
                          validators=[
                              InputRequired(message=INPUT_REQUIRED_MESSAGE),
                              Length(min=1, max=50, message="Максимальная длина - 50 символов"),
                              Regexp(NAME_SURNAME_REGEXP, message="Фамилия должна содержать только кириллицу"),
                          ])

    email = StringField("Адрес электронной почты", description="Введите email пользователя",
                        render_kw={"placeholder": "email@example.com", "maxlength": 50},
                        validators=[
                            InputRequired(message=INPUT_REQUIRED_MESSAGE),
                            Email(message="Невалидный формат email")
                        ])

    submit = SubmitField("Добавить")

    def validate_email(self, email: StringField) -> None:
        if UserCollection.has_email(email.data):
            raise ValidationError("Пользователь с таким email уже есть в системе!")
