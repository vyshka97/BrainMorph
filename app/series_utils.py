# -*- coding: utf-8 -*-

import os
import pydicom
import shutil
import tarfile
import hashlib
import numpy as np
import matplotlib.pyplot as plt

from flask import request, flash, Markup
from werkzeug.utils import secure_filename
from dicom2nifti.exceptions import ConversionError, ConversionValidationError
from collections import defaultdict, namedtuple
from dicom2nifti import dicom_series_to_nifti
from typing import List, Tuple
from glob import glob
from datetime import datetime
from wrapt_timeout_decorator import timeout
from operator import itemgetter
from nipype import Node, Workflow
from nipype.interfaces import fsl

from app import flask_app
from .model import PatientCollection, SeriesData, Series

__all__ = ["save_files_from_client", "split_on_series", "remove", "analyze"]

# для функции _get_series_info
__SeriesInfo = namedtuple("__SeriesInfo", ["id", "desc", "datetime"])
__SliceInfo = namedtuple("__SliceInfo", ["number"])


def save_files_from_client(patient_id: str) -> None:
    """
    Сохраняем все файлы, переданные клиентом, во временную папку
    """
    tmp_dir = os.path.join(flask_app.config['TMP_FOLDER'], patient_id)

    if not os.path.isdir(tmp_dir):
        os.makedirs(tmp_dir, exist_ok=True)

    upload_files = request.files.getlist("series")

    for file in upload_files:
        filename = secure_filename(file.filename)
        file.save(os.path.join(tmp_dir, filename))


def split_on_series(patient_id: str) -> None:
    """
    Распределяем загруженные срезы по сериям. Затем конвертируем в NIFTI.

    Проверяем каждый срез на теги.
    Если в хотя бы одном проверка не прошла, то ни одной серии не сохраняем.

    Проверяем каждую серию. Если серия не прошла проверку, то игнорим только ее.
    После сохранения и конвертации серии, сообщаем клиенту об этом.
    """

    series_data: SeriesData = PatientCollection.find_one(patient_id, SeriesData)

    tmp_dir = os.path.join(flask_app.config['TMP_FOLDER'], patient_id)
    dicom_dir = os.path.join(flask_app.config['DICOM_FOLDER'], patient_id)

    if not os.path.isdir(dicom_dir):
        os.makedirs(dicom_dir, exist_ok=True)

    series_id_to_paths = defaultdict(list)

    # здесь проверяем каждый срез перед тем, как замувить их в постоянную папку
    for slice_name in os.listdir(tmp_dir):
        slice_path = os.path.join(tmp_dir, slice_name)

        try:
            series_info, slice_info = _get_info_from_slice(slice_path)
        except AssertionError as e:
            flash(Markup(str(e)))
            continue

        series_id_to_paths[series_info].append((slice_info.number, slice_path))

    for series_info, values in series_id_to_paths.items():

        slice_paths = [slice_path for _, slice_path in sorted(values, key=lambda x: x[0])]

        if series_info.id in series_data.series_dict:
            flash(Markup(f"Серия <b>{series_info.desc}</b> уже хранится в системе"))
            continue

        try:
            _validate_series(slice_paths)
        except AssertionError as e:
            flash(Markup(str(e).format(series_info.desc)))
            continue

        last_dirname = hashlib.md5(series_info.id.encode()).hexdigest()
        series_dir = os.path.join(dicom_dir, last_dirname)

        img_dir = os.path.join(flask_app.config["SERIES_IMG_FOLDER"], patient_id, last_dirname)
        _make_series_images(slice_paths, img_dir)

        _move_series(slice_paths, series_dir)

        nifti_dir = os.path.join(flask_app.config["NIFTI_FOLDER"], patient_id, last_dirname)
        nifti_path = os.path.join(nifti_dir, "original" + flask_app.config["NIFTI_EXT"])

        _convert_series(series_dir, nifti_path, series_info.desc)
        archive_path = _archive_series(series_dir)

        series = Series(id=series_info.id, desc=series_info.desc, dt=series_info.datetime, dicom_path=archive_path,
                        nifti_dir=nifti_dir, img_dir=img_dir, slice_count=len(slice_paths))

        series_data.insert(series)

    # сохраняем пути в БД
    PatientCollection.save_data(series_data, patient_id=patient_id)

    # после всех операций удаляем временную папку
    shutil.rmtree(tmp_dir)


def remove(patient_id: str, series_id: str) -> None:
    """
    Удаляем серию: все снимки и запись в БД
    """

    # сначала удаляем запись из документа пациента
    series_data = PatientCollection.find_one(patient_id, SeriesData)
    series = series_data.find_or_404(series_id)
    desc, dicom_path, nifti_dir, img_dir = series.desc, series.dicom_path, series.nifti_dir, series.img_dir
    series_data.remove(series_id)
    PatientCollection.save_data(series_data, patient_id)

    # удаляем все пути
    os.remove(dicom_path)
    shutil.rmtree(nifti_dir)
    shutil.rmtree(os.path.join(flask_app.static_folder, img_dir))

    flash(Markup(f"Серия <b>{desc}</b> удалена"))


def analyze(patient_id: str, series_id: str) -> None:

    @timeout(720, use_signals=False)
    def run_workflow(wf: Workflow):
        return wf.run(plugin="MultiProc")

    series_data = PatientCollection.find_one(patient_id, SeriesData)
    series = series_data.find_or_404(series_id)

    nifti_dir = series.nifti_dir
    nifti_path = os.path.join(nifti_dir, "original.nii.gz")

    workflow = Workflow(name=os.path.basename(nifti_dir), base_dir=os.path.dirname(nifti_dir))

    frac = flask_app.config["BET_FRAC"]
    bet_interface = fsl.BET(in_file=os.path.abspath(nifti_path), frac=frac, robust=True)

    method = flask_app.config["FIRST_METHOD"]
    three_stage = flask_app.config["FIRST_THREE_STAGE"]
    first_interface = fsl.FIRST(method=method, brain_extracted=True, list_of_specific_structures=["L_Hipp", "R_Hipp"])
    if three_stage:
        first_interface.inputs.args = "-3"

    left_stats_interface = fsl.ImageStats(op_string="-l 16.5 -u 17.5 -V")
    right_stats_interface = fsl.ImageStats(op_string="-l 52.5 -u 53.5 -V")
    whole_brain_interface = fsl.ImageStats(op_string="-V")

    bet_node = Node(bet_interface, name="bet")
    first_node = Node(first_interface, name="first")
    left_stats_node = Node(left_stats_interface, name="left_stats")
    right_stats_node = Node(right_stats_interface, name="right_stats")
    whole_brain_node = Node(whole_brain_interface, name="whole_brain_stats")

    workflow.connect(bet_node, "out_file", first_node, "in_file")
    workflow.connect(first_node, "original_segmentations", left_stats_node, "in_file")
    workflow.connect(first_node, "original_segmentations", right_stats_node, "in_file")
    workflow.connect(bet_node, "out_file", whole_brain_node, "in_file")

    try:
        result_graph = run_workflow(workflow)
        result_nodes = list(result_graph.nodes)

        post_bet_path = result_nodes[0].result.outputs.out_file
        post_first_path = result_nodes[1].result.outputs.original_segmentations

        shutil.move(post_bet_path, os.path.join(nifti_dir, "post_bet.nii.gz"))
        shutil.move(post_first_path, os.path.join(nifti_dir, "post_first.nii.gz"))

        series.left_volume = round(result_nodes[2].result.outputs.out_stat[1], 3)
        series.right_volume = round(result_nodes[3].result.outputs.out_stat[1], 3)
        series.whole_brain_volume = round(result_nodes[4].result.outputs.out_stat[1], 3)
    except TimeoutError:
        series.error_type = "timeout"
    except RuntimeError:
        series.error_type = "runtime"

    paths_to_delete = set(glob(os.path.join(nifti_dir, "*"))) - set(glob(os.path.join(nifti_dir, "*.nii.gz")))
    for path in paths_to_delete:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

    series_data.insert(series)
    PatientCollection.save_data(series_data, patient_id)


def _convert_series(series_dir: str, nifti_path: str, series_desc: str) -> None:
    """
    Конвертируем DICOM серию в формат NIFTI.
    """
    nifti_dir = os.path.dirname(nifti_path)

    if not os.path.isdir(nifti_dir):
        os.makedirs(nifti_dir, exist_ok=True)

    try:
        dicom_series_to_nifti(series_dir, nifti_path)
        flash(Markup(f"Серия: <b>{series_desc}</b> успешно сохранена"))
    except (ConversionValidationError, ConversionError) as e:
        flash(str(e))
        shutil.rmtree(nifti_dir)


def _archive_series(series_dir: str) -> str:
    """
    Для экономии места на диске архивируем DICOM папку-серию.
    """
    archive_path = f"{series_dir}.tgz"

    with tarfile.open(archive_path, "w:gz") as _tar:
        _tar.add(series_dir, arcname=os.path.basename(series_dir))

    shutil.rmtree(series_dir)

    return archive_path


def _make_series_images(slice_paths: List[str], dir_path: str) -> None:
    """
    Отберем на примерно одинаковом расстоянии друг от друга срезы из переданного списка и
    сохраним в отдельной папке их изображения.
    """

    dir_path_ = os.path.join(flask_app.static_folder, dir_path)

    if not os.path.isdir(dir_path_):
        os.makedirs(dir_path_, exist_ok=True)

    img_ext = flask_app.config["SERIES_IMG_EXT"]

    if len(slice_paths) <= 10:
        paths_ = slice_paths
    else:
        indices = list(np.linspace(0, len(slice_paths) - 1, num=10, dtype=np.int))
        paths_ = itemgetter(*indices)(slice_paths)

    for path in paths_:
        header = pydicom.read_file(path)
        img_path = os.path.join(dir_path_, str(header.InstanceNumber)) + img_ext
        figure = plt.figure(figsize=(10, 10))
        plt.imshow(header.pixel_array, 'gray')
        plt.xticks([])
        plt.yticks([])
        plt.gca().set_axis_off()
        plt.savefig(img_path, bbox_inches='tight', pad_inches=0)
        plt.close(figure)


def _get_info_from_slice(slice_path: str) -> Tuple[__SeriesInfo, __SliceInfo]:
    """
    Вытаскиваем информацию из среза. Перед этим проверяем на наличие необходимых для конвертации тегов.
    """
    slice_name = os.path.basename(slice_path)
    header = pydicom.read_file(slice_path)

    assert "SeriesInstanceUID" in header, f"В снимке <b>{slice_name}</b> должен быть тег <b>SeriesInstanceUID</b>"
    assert "SeriesDescription" in header, f"В снимке <b>{slice_name}</b> должен быть тег <b>SeriesDescription</b>"
    assert "SeriesTime" in header, f"В снимке <b>{slice_name}</b> должен быть тег <b>SeriesTime</b>"
    assert "SeriesDate" in header, f"В снимке <b>{slice_name}</b> должен быть тег <b>SeriesDate</b>"
    assert "InstanceNumber" in header, f"В снимке <b>{slice_name}</b> должен быть тег <b>InstanceNumber</b>"
    assert "ImageOrientationPatient" in header, f"В снимке <b>{slice_name}</b> должен быть тег <b>ImageOrientationPatient</b>"
    assert "ImagePositionPatient" in header, f"В снимке <b>{slice_name}</b> должен быть тег <b>ImagePositionPatient</b>"

    assert len(header.ImageOrientationPatient) == 6, \
        f"В снимке <b>{slice_name}</b> длина тега <b>ImageOrientationPatient</b> должна равняться 6"
    assert len(header.ImagePositionPatient) == 3, \
        f"В снимке <b>{slice_name}</b> длина тега <b>ImagePositionPatient</b> должна равняться 3"

    time, date = header.SeriesTime.split(".")[0], header.SeriesDate
    series_datetime = datetime.strptime(f"{date} {time}", "%Y%m%d %H%M%S")

    series_info = __SeriesInfo(header.SeriesInstanceUID, header.SeriesDescription, series_datetime)
    slice_info = __SliceInfo(int(header.InstanceNumber))

    return series_info, slice_info


def _move_series(slice_paths: List[str], series_dir: str) -> None:
    """
    Мувим срезы из временной папки в папку для хранения DICOM серий.
    """
    if not os.path.isdir(series_dir):
        os.makedirs(series_dir, exist_ok=True)

    for slice_path in slice_paths:
        slice_name = os.path.basename(slice_path)
        new_slice_path = os.path.join(series_dir, slice_name)
        shutil.move(slice_path, new_slice_path)


def _validate_series(slice_paths: List[str]) -> None:
    """
    Проверяем, что кол-во срезов достаточно для создания выразительной серии
    https://github.com/icometrix/dicom2nifti/blob/6b8aeb0f291df57ea47aa2d945db84d6ff568903/dicom2nifti/common.py#L675
    """
    assert len(slice_paths) >= 4, "Количество загружаемых срезов в серии <b>{}</b> должно быть не меньше 4"

    first_image_orientation1, first_image_orientation2 = None, None

    for curr_slice_num, slice_path in enumerate(slice_paths, 1):
        header = pydicom.read_file(slice_path)

        slice_num = int(header.InstanceNumber)
        assert slice_num == curr_slice_num, f"В серии <b>{{}}</b> не хватает среза под номером <b>{curr_slice_num}</b>"

        """
        Проверяем, что все срезы имеют одинаковую ориентацию
        https://github.com/icometrix/dicom2nifti/blob/6b8aeb0f291df57ea47aa2d945db84d6ff568903/dicom2nifti/common.py#L688
        """

        if first_image_orientation1 is None:
            first_image_orientation1 = np.asarray(header.ImageOrientationPatient)[0:3]
            first_image_orientation2 = np.asarray(header.ImageOrientationPatient)[3:6]

        image_orientation1 = np.asarray(header.ImageOrientationPatient)[0:3]
        image_orientation2 = np.asarray(header.ImageOrientationPatient)[3:6]

        is_equal1 = np.allclose(image_orientation1, first_image_orientation1, rtol=0.001, atol=0.001)
        is_equal2 = np.allclose(image_orientation2, first_image_orientation2, rtol=0.001, atol=0.001)

        assert is_equal1 and is_equal2, "В серии <b>{}</b> значения <b>ImageOrientationPatient</b> неконсистентны"

    assert _is_orthogonal(slice_paths), "Изображение серии <b>{}</b> не 3D"


def _is_orthogonal(slice_paths: List[str]) -> bool:
    """
    Проверяем, что серия ортонормирована
    https://github.com/icometrix/dicom2nifti/blob/6b8aeb0f291df57ea47aa2d945db84d6ff568903/dicom2nifti/common.py#L550
    """
    first_header = pydicom.read_file(slice_paths[0])
    last_header = pydicom.read_file(slice_paths[-1])

    first_image_orientation1 = np.array(first_header.ImageOrientationPatient)[0:3]
    first_image_orientation2 = np.array(first_header.ImageOrientationPatient)[3:6]

    first_image_position = np.array(first_header.ImagePositionPatient)
    last_image_position = np.array(last_header.ImagePositionPatient)

    first_image_direction = np.cross(first_image_orientation1, first_image_orientation2)
    first_image_direction /= np.linalg.norm(first_image_direction)

    combined_dir = last_image_position - first_image_position
    combined_dir /= np.linalg.norm(combined_dir)

    check1 = np.allclose(first_image_direction, combined_dir, rtol=0.05, atol=0.05)
    check2 = np.allclose(first_image_direction, -combined_dir, rtol=0.05, atol=0.05)

    return check1 or check2
