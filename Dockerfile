FROM ubuntu:18.04

RUN apt-get update && apt-get install -y wget python python3.6 python3-venv python3-dev \
    mongodb git libgl1-mesa-dev g++ dc bc

RUN wget https://fsl.fmrib.ox.ac.uk/fsldownloads/fslinstaller.py && \
    python2 fslinstaller.py -V 6.0.2 -d /usr/local/fsl

# setup FSL environment
ENV FSLDIR="/usr/local/fsl"
ENV PATH="$FSLDIR/bin:$PATH"
ENV FSLOUTPUTTYPE="NIFTI_GZ"

WORKDIR /brain_morph

COPY requirements.txt ./requirements.txt
RUN python3 -m venv ./venv
RUN venv/bin/pip install wheel 
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn

COPY app app
COPY brain_morph.py config.py boot.sh nipype.cfg ./
RUN mkdir -p /data/db
RUN chmod a+x boot.sh

ENV FLASK_APP brain_morph.py

CMD ./boot.sh $PORT
