# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    # Flask и некоторые его расширения используют значение секретного ключа в качестве криптографического ключа,
    # полезного для генерации подписей или токенов.
    SECRET_KEY = os.environ.get("SECRET_KEY") or "OY4U3OpCHx"

    ADMIN_NAME = os.environ.get("ADMIN_NAME", "Максим")
    ADMIN_SURNAME = os.environ.get("ADMIN_SURNAME", "Вышегородцев")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "maks@yandex.ru")
    ADMIN_LOGIN = os.environ.get("ADMIN_LOGIN", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "adminpass")

    # настройки Mongo DB
    MONGODB_DB = os.environ.get("MONGODB_DB") or "BrainMorph"
    MONGODB_HOST = os.environ.get("MONGODB_HOST") or "0.0.0.0"
    MONGODB_PORT = os.environ.get("MONGODB_PORT") or 27017

    MONGO_URI = f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DB}"

    MONGODB_USERNAME = os.environ.get("MONGODB_USERNAME")
    MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD")

    # настройки для подключения к почтовому серверу
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or "smtp.gmail.com"
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') or True
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL") or False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or "noreply.brain.morph@gmail.com"
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or "Dc95jWFdT9EFfUb"
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER") or ("Brain Morph", "noreply@brain-morph.ru")

    # количество выводимых записей пациентов в пагинации на главной странице
    PATIENTS_PAGE_SIZE = os.environ.get("PATIENTS_PAGE_SIZE") or 3

    # временная папка для загрузки файлов с клиента. Путь задается относительно корня проекта.
    TMP_FOLDER = os.environ.get("TMP_FOLDER") or "TMP"

    # папка для хранения DICOM снимков. Путь задается относительно корня проекта.
    DICOM_FOLDER = os.environ.get("DICOM_FOLDER") or "DICOM_SERIES"

    # папка для хранения NIFTI серий. Путь задается относительно корня проекта.
    NIFTI_FOLDER = os.environ.get("NIFTI_FOLDER") or "NIFTI_SERIES"

    # расширение NIFTI
    NIFTI_EXT = os.environ.get("NIFTI_EXT") or ".nii.gz"

    # папка для 2D хранения изображений серий. Путь задается относительно static папки приложения.
    SERIES_IMG_FOLDER = os.environ.get("SERIES_IMG_FOLDER") or "SERIES_IMAGE"

    # расширение для 2D изображений серий
    SERIES_IMG_EXT = os.environ.get("SERIES_IMG_EXT") or ".png"

    # fractional intensity threshold для FSL BET (параметр -f)
    BET_FRAC = float(os.environ.get("BET_FRAC") or 0.8)

    # Метод корректировки границ выделенных структур для FSL FIRST (параметр -m)
    FIRST_METHOD = os.environ.get("FIRST_METHOD") or "none"

    # Флаг для включения 3-х этапной регистрации в FSL FIRST (по умолчанию проводится 2-х этапная)
    FIRST_THREE_STAGE = bool(os.environ.get("FIRST_THREE_STAGE") or False)

    # путь до папки, куда складывать файлы с описанием падения nipype workflow.
    # Путь задается относительно корня проекта.
    NIPYPE_CRASH_DIR = os.environ.get("NIPYPE_CRASH_DIR") or "NIPYPE_CRASHES"

    # таймаут в секундах для анализа. По умолчанию ставим 12 минут
    TIMEOUT_VALUE = os.environ.get("TIMEOUT_VALUE", 720)
