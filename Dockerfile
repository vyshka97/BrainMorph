FROM ubuntu:18.04

# установка python и необходимых для FSL библиотек
RUN apt-get update && apt-get install -y wget python python3.6 python3-venv python3-dev \
    mongodb git libgl1-mesa-dev g++ dc bc

# загружаем установочный скрипт FSL
RUN wget https://fsl.fmrib.ox.ac.uk/fsldownloads/fslinstaller.py && \
    python2 fslinstaller.py -V 6.0.2 -d /usr/local/fsl

# setup FSL environment
ENV FSLDIR="/usr/local/fsl"
ENV PATH="$FSLDIR/bin:$PATH"
ENV FSLOUTPUTTYPE="NIFTI_GZ"

# рабочая папка
WORKDIR /brain_morph

# устанавливаем виртуальное окружение
COPY requirements.txt ./requirements.txt
RUN python3 -m venv ./venv
RUN venv/bin/pip install wheel 
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn

# копируем необходимые файлы
COPY app app
COPY brain_morph.py config.py boot.sh nipype.cfg ./
RUN mkdir -p /data/db
RUN chmod a+x boot.sh

# переменная окруженная для запуска приложения
ENV FLASK_APP brain_morph.py

# точка входа при запуске контейнера
CMD ./boot.sh $PORT
