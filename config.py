# -*- coding: utf-8 -*-

import os


class Config:
    # Flask и некоторые его расширения используют значение секретного ключа в качестве криптографического ключа,
    # полезного для генерации подписей или токенов.
    SECRET_KEY = os.environ.get("SECRET_KEY") or "OY4U3OpCHx"

    # настройки Mongo DB
    MONGODB_DB = os.environ.get("MONGODB_DB") or "BrainMorph"
    MONGODB_HOST = os.environ.get("MONGODB_HOST") or "localhost"
    MONGODB_PORT = os.environ.get("MONGODB_PORT") or 27017

    MONGO_URI = f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DB}"

    MONGODB_USERNAME = os.environ.get("MONGODB_USERNAME")
    MONGODB_PASSWORD = os.environ.get("MONGODB_PASSWORD")

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
