# -*- coding: utf-8 -*-

import random
import string
import os

from attr import attrs, attrib, fields, asdict
from datetime import datetime
from flask_pymongo import ObjectId
from typing import List, Any, Dict, Tuple
from flask import abort
from flask_login import UserMixin
from werkzeug.security import check_password_hash
from docx import Document

from app import patients, flask_app, login, users

__all__ = ["RegistrationData", "PrimaryData", "SecondaryBiomarkers", "SeriesData", "Series",
           "PatientCollection", "Patient", "User", "UserCollection"]

@attrs
class _PatientData:
    FIELD_NAME = ""

    id = None

    def serialize(self) -> Dict[str, Any]:
        return {self.__class__.FIELD_NAME: asdict(self, filter=lambda _, value: value is not None)}

    @classmethod
    def create_from_dict(cls, data: Dict[str, Any]) -> "_PatientData":
        instance = cls(**data.get(cls.FIELD_NAME, {}))
        instance.id = data.get("_id")
        return instance


@attrs(repr=False)
class RegistrationData(_PatientData):
    FIELD_NAME = "registration_data"

    name = attrib(type=str)
    surname = attrib(type=str)
    birthday = attrib(type=datetime)
    mobile_number = attrib(type=str)

    @property
    def age(self) -> int:
        return (datetime.now() - self.birthday).days // 365

    def __repr__(self) -> str:
        return f"Фамилия: {self.surname}\n" \
               f"Имя: {self.name}\n" \
               f"Возраст: {self.age} лет\n" \
               f"Номер мобильного телефона: +7{self.mobile_number}"


@attrs(repr=False)
class PrimaryData(_PatientData):
    FIELD_NAME = "primary_data"

    height = attrib(type=int, default=None)
    weight = attrib(type=int, default=None)
    is_smoking = attrib(type=bool, default=None)
    complaints = attrib(type=str, default=None)

    def __repr__(self) -> str:
        return f"Рост: {self.height} см\n" \
               f"Вес: {self.weight} кг\n" \
               f"Курит?: {'да' if self.is_smoking else 'нет'}\n" \
               f"Жалобы: {self.complaints}"


@attrs(repr=False)
class SecondaryBiomarkers(_PatientData):
    FIELD_NAME = "secondary_biomarkers"

    mmse = attrib(type=int, default=None)
    moca = attrib(type=int, default=None)

    def __repr__(self) -> str:
        return f"MMSE: {self.mmse}\n" \
               f"MoCA: {self.moca}"


@attrs(slots=True, repr=False)
class Series:
    id = attrib(type=str)
    desc = attrib(type=str)
    dt = attrib(type=datetime)

    slice_count = attrib(type=int)

    dicom_path = attrib(type=str)
    nifti_dir = attrib(type=str)
    img_dir = attrib(type=str)

    # данные, полученные после проведения морфометического анализа
    whole_brain_volume = attrib(type=float, default=None)
    left_volume = attrib(type=float, default=None)
    right_volume = attrib(type=float, default=None)
    error_type = attrib(type=str, default=None)  # timeout or runtime

    @property
    def normed_left_volume(self) -> float:
        if self.left_volume is not None and self.whole_brain_volume is not None:
            return round(self.left_volume / self.whole_brain_volume, 5)

    @property
    def normed_right_volume(self) -> float:
        if self.right_volume is not None and self.whole_brain_volume is not None:
            return round(self.right_volume / self.whole_brain_volume, 5)

    @property
    def image_paths(self) -> List[str]:
        img_dir = os.path.join(flask_app.static_folder, self.img_dir)
        sorted_list_dir = sorted(os.listdir(img_dir), key=lambda x: int(x.split('.')[0]))
        return [os.path.join(self.img_dir, basename) for basename in sorted_list_dir]

    def __repr__(self) -> str:
        return f"Идентификатор: {self.id}\n" \
               f"Дата и время создания: {self.dt}\n" \
               f"Объем левого гиппокампа: {self.left_volume} мм\u00b3\n" \
               f"Объем правого гиппокампа: {self.right_volume} мм\u00b3\n" \
               f"Объем мозговой ткани: {self.whole_brain_volume} мм\u00b3\n" \
               f"Нормализованный объем левого гиппокампа: {self.normed_left_volume}\n" \
               f"Нормализованный объем правого гиппокампа: {self.normed_right_volume}"


@attrs
class SeriesData(_PatientData):
    FIELD_NAME = "series_data"

    series_dict = attrib(type=Dict[str, Series], default={})

    def __len__(self) -> int:
        return len(self.series_dict)

    def find_or_404(self, series_id: str) -> Series:
        if series_id not in self.series_dict:
            abort(404)

        return Series(**self.series_dict[series_id])

    def find_all(self) -> List[Series]:
        return [Series(**data) for data in self.series_dict.values()]

    def insert(self, series: Series) -> None:
        self.series_dict[series.id] = series

    def remove(self, series_id: str) -> bool:
        if series_id not in self.series_dict:
            return False

        del self.series_dict[series_id]
        return True


@attrs
class Patient(_PatientData):
    registration_data = attrib(type=RegistrationData)
    primary_data = attrib(type=PrimaryData, default=None)
    secondary_biomarkers = attrib(type=SecondaryBiomarkers, default=None)
    series_data = attrib(type=SeriesData, default=None)

    def get_report(self) -> Document:
        document = Document()
        document.add_heading("Отчет", level=0)

        document.add_heading("Регистрационные данные", level=1)
        document.add_paragraph(repr(self.registration_data))

        document.add_heading("Первичные данные", level=1)
        document.add_paragraph(repr(self.primary_data))

        document.add_heading("Другие биомаркеры", level=1)
        document.add_paragraph(repr(self.secondary_biomarkers))

        document.add_heading("Серии", level=1)
        for series in self.series_data.find_all():
            document.add_heading(f"Серия: {series.desc}", level=2)
            document.add_paragraph(repr(series))

        return document

    @classmethod
    def create_from_dict(cls, data: Dict[str, Any]) -> "Patient":
        instance = cls(**{field.name: field.type(**data.get(field.type.FIELD_NAME, {})) for field in fields(Patient)})
        instance.id = data.get("_id")
        return instance


@attrs
class User(UserMixin):
    id = attrib(type=str)
    password_hash = attrib(type=str)
    email = attrib(type=str)
    name = attrib(type=str)
    surname = attrib(type=str)
    is_admin = attrib(type=bool, default=False)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @classmethod
    def create_from_dict(cls, data: Dict[str, Any]) -> "User":
        data["id"] = data["_id"]
        del data["_id"]
        return cls(**data)

    @staticmethod
    def generate_login_password(email: str) -> Tuple[str, str]:
        password_len = random.randint(8, 16)
        password = ''.join(random.sample(string.ascii_letters + string.digits, k=password_len))
        return email.split("@")[0], password


class UserCollection:

    @staticmethod
    @login.user_loader
    def find_one(user_id: str) -> User:
        data = users.find_one({"_id": user_id})
        if data is not None:
            return User.create_from_dict(data)

    @staticmethod
    def has_email(email: str) -> bool:
        return users.find_one({"email": email}) is not None

    @staticmethod
    def find_one_or_404(user_id: str) -> User:
        data = users.find_one_or_404({"_id": ObjectId(user_id)})
        return User.create_from_dict(data)

    @staticmethod
    def find_all() -> List[User]:
        return [User.create_from_dict(data) for data in users.find()]

    @staticmethod
    def save_data(data: User) -> None:
        users.update_one({"_id": data.id}, {'$set': asdict(data)}, upsert=True)

    @staticmethod
    def delete_one(user_id: str) -> None:
        users.delete_one({"_id": user_id})


class PatientCollection:

    PAGE_SIZE = flask_app.config["PATIENTS_PAGE_SIZE"]

    @staticmethod
    def find_one(patient_id: str, cls: type = None) -> _PatientData:
        PatientCollection.__cls_check(cls)

        _cls = cls or Patient

        if _cls == Patient:
            data = patients.find_one_or_404({"_id": ObjectId(patient_id)})
        else:
            data = patients.find_one_or_404({"_id": ObjectId(patient_id)}, {cls.FIELD_NAME: 1})

        return _cls.create_from_dict(data)

    @staticmethod
    def find_all(cls: type = None) -> List[_PatientData]:
        _cls = cls or Patient
        return [_cls.create_from_dict(data) for data in patients.find()]

    @staticmethod
    def delete_field(patient_id: str, cls: type) -> None:
        PatientCollection.__cls_check(cls)
        patients.update_one({"_id": ObjectId(patient_id)}, {"$unset": {cls.FIELD_NAME: ""}})

    @staticmethod
    def save_data(data: _PatientData, patient_id: str = None) -> str:
        if patient_id:
            patients.update_one({"_id": ObjectId(patient_id)}, {'$set': data.serialize()})
            return patient_id
        else:
            inserted = patients.insert_one(data.serialize())
            return str(inserted.inserted_id)

    @staticmethod
    def paginate(page_num: int, cls: type = None, sort_rules: Dict[str, int] = None) -> Tuple[List[_PatientData], bool, bool]:
        PatientCollection.__cls_check(cls)

        _cls = cls or Patient

        if _cls == Patient:
            cursor = patients.find()
        else:
            cursor = patients.find({}, {_cls.FIELD_NAME: 1})

        if sort_rules is not None:
            cursor = cursor.sort(list(sort_rules.items()))

        skip_cnt = PatientCollection.PAGE_SIZE * (page_num - 1)
        cursor = cursor.skip(skip_cnt).limit(PatientCollection.PAGE_SIZE)
        
        docs = [_cls.create_from_dict(data) for data in cursor]

        has_next = patients.estimated_document_count() > page_num * PatientCollection.PAGE_SIZE
        has_prev = page_num > 1
            
        return docs, has_next, has_prev

    @staticmethod
    def __cls_check(cls: type = None) -> None:
        if cls is not None and not issubclass(cls, _PatientData):
            raise ValueError(f"Passed class must be a subclass of {_PatientData.__name__}")
