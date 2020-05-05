# -*- coding: utf-8 -*-

from threading import Thread
from flask import render_template, current_app
from flask_mail import Message

from app.model import User
from app import mail


def send_login_password(user: User) -> None:
    msg = Message("[BrainMorph] Доступ к системе", recipients=[user.email],
                  html=render_template("email/login_password.html", user=user))
    Thread(target=_send_async_email, args=(current_app._get_current_object(), msg)).start()


def _send_async_email(app, msg) -> None:
    """
    Отправляем email-сообщение асинхронно
    """
    with app.app_context():
        mail.send(msg)
