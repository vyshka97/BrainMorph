# -*- coding: utf-8 -*-

from attr import attrs, attrib, fields, asdict
from datetime import datetime
from flask_pymongo import ObjectId
from typing import List, Any, Dict, Tuple
from flask import abort
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

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


@attrs
class RegistrationData(_PatientData):
    FIELD_NAME = "registration_data"

    name = attrib(type=str)
    surname = attrib(type=str)
    birthday = attrib(type=datetime)
    mobile_number = attrib(type=str)

    @property
    def age(self) -> int:
        return (datetime.now() - self.birthday).days // 365


@attrs
class PrimaryData(_PatientData):
    FIELD_NAME = "primary_data"

    height = attrib(type=int, default=None)
    weight = attrib(type=int, default=None)
    is_smoking = attrib(type=bool, default=None)
    complaints = attrib(type=str, default=None)


@attrs
class SecondaryBiomarkers(_PatientData):
    FIELD_NAME = "secondary_biomarkers"

    mmse = attrib(type=int, default=None)
    moca = attrib(type=int, default=None)


@attrs(slots=True)
class Series:
    id = attrib(type=str)
    desc = attrib(type=str)
    dt = attrib(type=datetime)

    dicom_path = attrib(type=str)
    nifti_dir = attrib(type=str)
    img_path = attrib(type=str)

    whole_brain_volume = attrib(type=float, default=None)
    left_volume = attrib(type=float, default=None)
    right_volume = attrib(type=float, default=None)

    @property
    def normed_left_volume(self) -> float:
        if self.left_volume is not None and self.whole_brain_volume is not None:
            return round(self.left_volume / self.whole_brain_volume, 5)

    @property
    def normed_right_volume(self) -> float:
        if self.right_volume is not None and self.whole_brain_volume is not None:
            return round(self.right_volume / self.whole_brain_volume, 5)


@attrs
class SeriesData(_PatientData):
    FIELD_NAME = "series_data"

    series_dict = attrib(type=Dict[str, Series], default={})

    def find_or_404(self, series_id: str) -> Series:
        if series_id not in self.series_dict:
            abort(404)

        return self.series_dict[series_id]

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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def create_from_dict(cls, data: Dict[str, Any]) -> "User":
        data["id"] = data["_id"]
        del data["_id"]
        return cls(**data)


class UserCollection:

    @staticmethod
    @login.user_loader
    def find_one(user_id: str) -> User:
        data = users.find_one({"_id": user_id})
        if data is not None:
            return User.create_from_dict(data)

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
    def save_data(data: _PatientData, patient_id: str = None) -> None:
        if patient_id:
            patients.update_one({"_id": ObjectId(patient_id)}, {'$set': data.serialize()})
        else:
            patients.insert_one(data.serialize())

    @staticmethod
    def paginate(page_num: int, cls: type, sort_rules: Dict[str, int] = None) -> Tuple[List[_PatientData], bool, bool]:
        PatientCollection.__cls_check(cls)

        cursor = patients.find({}, {cls.FIELD_NAME: 1})
        if sort_rules is not None:
            cursor = cursor.sort(list(sort_rules.items()))

        skip_cnt = PatientCollection.PAGE_SIZE * (page_num - 1)
        cursor = cursor.skip(skip_cnt).limit(PatientCollection.PAGE_SIZE)
        
        docs = [cls.create_from_dict(data) for data in cursor]

        has_next = patients.estimated_document_count() > page_num * PatientCollection.PAGE_SIZE
        has_prev = page_num > 1
            
        return docs, has_next, has_prev

    @staticmethod
    def __cls_check(cls: type = None) -> None:
        if cls is not None and not issubclass(cls, _PatientData):
            raise ValueError(f"Passed class must be a subclass of {_PatientData.__name__}")
