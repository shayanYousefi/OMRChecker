#!/usr/bin/env python3

from pathlib import Path
from os import getenv
from src.queue.client import amqp_connect
from dotenv import load_dotenv


def create_inputs_folder():
    Path(getenv("INPUT_FOLDER")).mkdir(exist_ok=True)


def create_outputs_folder():
    Path(getenv("OUTPUT_FOLDER")).mkdir(exist_ok=True)


def consume_from_amqp(url):
    amqp_connect(url)


if __name__ == "__main__":

    load_dotenv()
    create_inputs_folder()
    create_outputs_folder()

    amqp_url = getenv("RABIIT_CONNECTION_URL",
                      "amqp://guest:guest@localhost:5672/")

    consume_from_amqp(amqp_url)
