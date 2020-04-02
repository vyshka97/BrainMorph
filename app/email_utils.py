# -*- coding: utf-8 -*-

from threading import Thread
from flask import render_template
from flask_sendmail import Message

from .model import User
from app import flask_app, mail, ViewPage


def send_login_password(user: User, password: str) -> None:
    msg = Message("[BrainMorph] Доступ к системе", recipients=[user.email],
                  html=render_template(ViewPage.EMAIL.value, user=user, password=password))
    Thread(target=_send_async_email, args=(flask_app, msg)).start()


def _send_async_email(app, msg) -> None:
    """
    Отправляем email-сообщение асинхронно
    """
    with app.app_context():
        mail.send(msg)
