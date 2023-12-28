#!/usr/bin/env python3

from pathlib import Path
from os import getenv
from src.queue.client import amqp_connect
from dotenv import load_dotenv
import boto3


def create_inputs_folder():
    Path(getenv("INPUT_FOLDER")).mkdir(exist_ok=True)


def create_outputs_folder():
    Path(getenv("OUTPUT_FOLDER")).mkdir(exist_ok=True)


def consume_from_amqp(url, s3_client):
    amqp_connect(url, s3_client)


if __name__ == "__main__":

    load_dotenv()
    create_inputs_folder()
    create_outputs_folder()

    amqp_url = getenv("RABIIT_CONNECTION_URL",
                      "amqp://guest:guest@localhost:5672/")

    s3_client = boto3.client('s3', endpoint_url=getenv("S3_ENDPOINT"),
                             aws_secret_access_key=getenv("S3_SECRET_KEY"),
                             aws_access_key_id=getenv("S3_ACCESS_KEY"))
    consume_from_amqp(amqp_url, s3_client)
