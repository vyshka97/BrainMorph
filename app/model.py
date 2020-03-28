# -*- coding: utf-8 -*-

from attr import attrs, attrib, fields, asdict
from datetime import datetime
from flask_pymongo import ObjectId, ASCENDING
from pymongo.cursor import Cursor
from typing import List, Any, Dict
from flask import abort

from app import patients, flask_app


@attrs
class _PatientData:
    FIELD_NAME = ""

    id = None

    def serialize(self) -> Dict[str, Any]:
        return {self.__class__.FIELD_NAME: asdict(self)}

    @classmethod
    def create_from_dict(cls, data: Dict[str, Any]) -> "_PatientData":
        return cls(**data.get(cls.FIELD_NAME, {}))


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
    nifti_path = attrib(type=str)
    img_path = attrib(type=str)


@attrs
class SeriesData(_PatientData):
    FIELD_NAME = "series_data"

    series_dict = attrib(type=Dict[str, Series], default={})

    def find_or_404(self, series_id: str) -> Series:
        if series_id not in self.series_dict:
            abort(404)

        return self.series_dict[series_id]

    def append(self, series: Series) -> None:
        self.series_dict[series.id] = series

    def remove(self, series_id: str) -> bool:
        if series_id not in self.series_dict:
            return False

        del self.series_dict[series_id]
        return True

    @classmethod
    def create_from_dict(cls, data: Dict[str, Any]) -> "SeriesData":
        instance = cls(**data.get(cls.FIELD_NAME, {}))
        instance.series_dict = {series_id: Series(**dct) for series_id, dct in instance.series_dict.items()}
        return instance


@attrs
class Patient(_PatientData):
    registration_data = attrib(type=RegistrationData)
    primary_data = attrib(type=PrimaryData, default=None)
    secondary_biomarkers = attrib(type=SecondaryBiomarkers, default=None)
    series_data = attrib(type=SeriesData, default=None)

    @classmethod
    def create_from_dict(cls, data: Dict[str, Any]) -> "Patient":
        return cls(**{field.name: field.type(**data.get(field.type.FIELD_NAME, {})) for field in fields(Patient)})


class PatientCollection:

    PAGE_SIZE = flask_app.config["PATIENTS_PAGE_SIZE"]

    @staticmethod
    def find_one(patient_id: str, data_class: type) -> Any:
        if data_class == Patient:
            data = patients.find_one_or_404({"_id": ObjectId(patient_id)})
        else:
            data = patients.find_one_or_404({"_id": ObjectId(patient_id)}, {data_class.FIELD_NAME: 1})

        instance = data_class.create_from_dict(data)
        instance.id = patient_id

        return instance

    @staticmethod
    def count_documents() -> int:
        return patients.estimated_document_count()

    @staticmethod
    def find_all() -> Cursor:
        return patients.find()

    @staticmethod
    def delete_field(patient_id: str, data_class: type) -> None:
        patients.update_one({"_id": ObjectId(patient_id)}, {"$unset": {data_class.FIELD_NAME: ""}})

    @staticmethod
    def save_data(data: _PatientData, patient_id: str = None) -> None:
        if patient_id:
            patients.update_one({"_id": ObjectId(patient_id)}, {'$set': data.serialize()})
        else:
            patients.insert_one(data.serialize())

    @staticmethod
    def get_registration_data_page(page_num: int) -> List[RegistrationData]:
        sort_rules = [
            (f"{RegistrationData.FIELD_NAME}.surname", ASCENDING),
            (f"{RegistrationData.FIELD_NAME}.name", ASCENDING)
        ]

        cursor = patients.find({}, {RegistrationData.FIELD_NAME: 1}).sort(sort_rules)
        skip_cnt = PatientCollection.PAGE_SIZE * (page_num - 1)
        
        docs = []
        for data in cursor.skip(skip_cnt).limit(PatientCollection.PAGE_SIZE):
            instance = RegistrationData(**data[RegistrationData.FIELD_NAME])
            instance.id = data["_id"]
            docs.append(instance)
            
        return docs

    @staticmethod
    def has_next_page(page_num: int) -> bool:
        return PatientCollection.count_documents() > page_num * PatientCollection.PAGE_SIZE

    @staticmethod
    def has_prev_page(page_num: int) -> bool:
        return page_num > 1
