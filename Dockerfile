FROM python:3.11-slim

WORKDIR /var/app

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update -y && \
    apt install -y build-essential cmake unzip pkg-config \
    libjpeg-dev libpng-dev libtiff-dev \
    libavcodec-dev libavformat-dev libswscale-dev libv4l-dev \
    libatlas-base-dev gfortran


COPY ./ /var/app/

RUN pip3 install --user opencv-python-headless opencv-contrib-python-headless
RUN pip3 install -r requirements.txt

RUN apt clean
RUN apt -y autoremove
RUN pip3 cache purge

#Set env to know if app is running in container 
ENV CONTAINER_MODE True
ENV SOALAA_URL "https://soalaa.com/api/v1/exam/save-paper-sheets-excel"
ENV SOALAA_TOKEN "token"

ENV RABIIT_CONNECTION_URL "amqp://guest:guest@localhost:5672/"
ENV RABBIT_EXCHANGE "3a"
ENV RABBIT_AZMOONS_QUEUE "azmoons_correction"
ENV RABBIT_AZMOONS_ROUTING_KEY "correct-paper-sheets"

ENV S3_ENDPOINT "https://s3.com"
ENV S3_ACCESS_KEY "key"
ENV S3_SECRET_KEY "secret"
ENV S3_BUCKET "aaa"
ENV S3_PREFIX "OMR/CheckedFiles"

ENV INPUT_FOLDER "/var/app/inputs/scans"
ENV OUTPUT_FOLDER "/var/app/outputs/scans"

ENV LOG_LEVEL "info"


## Run the default command
CMD ["python", "/var/app/main.py"]