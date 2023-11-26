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
ENV CONTAINER_MODE=True

## Run the default command
CMD ["python", "/var/app/main.py"]