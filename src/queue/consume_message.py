from pathlib import Path
from zipfile import ZipFile
from os import getenv, sep
import pandas
import requests
import boto3
from shutil import rmtree

import main
import src.result_manipulation as result_manipulation
from ..utils.file import empty_folder
from ..logger import logger


def download_pics(url, full_dest_path):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(full_dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return full_dest_path


def unzip_pics(zip_filepath, dest_dir):
    with ZipFile(zip_filepath, 'r') as zip_ref:
        zip_ref.extractall(dest_dir)


def remove_zip_file(zip_filepath):
    Path(zip_filepath).unlink()


def get_file_count(dir):
    files = Path(dir).glob("*")
    files = list(files)
    return len(files)


def flatten_directory(root):
    root = Path(root)
    files = []
    folders = []
    paths = list(root.glob("**/*"))
    for path in paths:
        if path.is_dir():
            folders.append(path)
            continue
        elif path.is_file():
            route = str(path.resolve())
            route = route.replace(f"{root.resolve()}{sep}", '')
            route = route.replace(sep, '_')
            files.append((path.resolve(), route))
    for file_path, new_name in files:
        file_path.replace(root.joinpath(new_name))
    for folder in folders:
        if folder.exists():
            rmtree(str(folder))


def get_result_file_path(output_dir):
    files = Path(output_dir).glob("Results_*.csv")
    files = list(files)
    return str(files[0].resolve())


def populate_request_headers(token):
    return {'Authorization': f"Bearer {token}",
            'Accept': "application/json"
            }


def send_result_to_soalaa(file_path, file_count, file_name):
    url = getenv("SOALAA_URL")
    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f, 'text/csv')}
        request_body = {'count': file_count, 'unique-zip-file-name': file_name}
        request_headers = populate_request_headers(getenv('SOALAA_TOKEN'))
        response = requests.post(
            url, data=request_body, files=files, headers=request_headers)
        response.raise_for_status()
        return response


def upload_image_results_to_s3(file_list, folder_name, s3_client):
    destination_list = {}
    for file in file_list:
        destination = f"{getenv('S3_PREFIX')}/{folder_name}/{file.name}"
        s3_client.upload_file(file.resolve(), getenv("S3_BUCKET"), destination)
        cdn_base = getenv("S3_CDN") if getenv(
            "S3_CDN") else getenv("S3_ENDPOINT")
        full_url = "{}/{}/{}".format(
            cdn_base, getenv("S3_BUCKET"), destination)
        destination_list[file.name] = full_url
    return destination_list


def get_list_of_image_results(folder):
    image_files = []
    image_files.extend(Path(folder).glob("*.jpg"))
    image_files.extend(Path(folder).glob("*.png"))
    return image_files


def add_upload_url_to_csv(file_path, image_url_list, new_file_location):
    upload_url_column_name = "file_checked_url"
    csv_file = pandas.read_csv(file_path)
    result_manipulation.add_file_result_url(
        csv_file, upload_url_column_name)
    result_manipulation.populate_file_result_url(
        csv_file, image_url_list, upload_url_column_name)
    return result_manipulation.save_new_file(csv_file, new_file_location)


def process_message(body):
    s3_client = boto3.client('s3', endpoint_url=getenv("S3_ENDPOINT"),
                             aws_secret_access_key=getenv("S3_SECRET_KEY"),
                             aws_access_key_id=getenv("S3_ACCESS_KEY"))
    url = body.decode('utf-8')
    zip_file_name = url.split('/')[-1]
    file_path = Path(f"{getenv('INPUT_FOLDER')}/{zip_file_name}")

    logger.debug(f"Clearing {getenv('INPUT_FOLDER')} folder")
    empty_folder(getenv("INPUT_FOLDER"))
    logger.debug(f"Clearing {getenv('OUTPUT_FOLDER')} folder")
    empty_folder(getenv("OUTPUT_FOLDER"))
    logger.debug(f"Downloading {url}")
    download_pics(url, file_path.resolve())

    pics_folder = f"{file_path.parent}/{file_path.stem}"
    logger.debug(f"Unziping {file_path.resolve()}")
    unzip_pics(file_path.resolve(), pics_folder)
    remove_zip_file(file_path.resolve())
    flatten_directory(pics_folder)

    file_count = get_file_count(pics_folder)
    logger.debug(f"Found {file_count} file in compressed file")
    args = {
        "input_paths": ["inputs"],
        "debug": False,
        "output_dir": "outputs",
        "autoAlign": False,
        "setLayout": False,
    }
    logger.debug(f"processing files in  {file_path.resolve()}")
    main.entry_point_for_args(args)
    output_dir = f"{getenv('OUTPUT_FOLDER')}/{file_path.stem}/Results"
    result_path = get_result_file_path(output_dir)

    image_result_folder = "{}/{}/CheckedOMRs".format(
        getenv('OUTPUT_FOLDER'), file_path.stem)
    image_result_list = get_list_of_image_results(image_result_folder)

    logger.debug("Uploading result sheets to s3")
    image_url_list = upload_image_results_to_s3(
        image_result_list, file_path.stem, s3_client)
    changed_result_file = f"{output_dir}/{file_path.stem}.csv"
    add_upload_url_to_csv(result_path, image_url_list, changed_result_file)

    logger.info("Sending csv result to soalaa")
    response = send_result_to_soalaa(
        changed_result_file, file_count, zip_file_name)
    logger.info(f"Response of soalaa: {response}")

    logger.debug(f"Clearing {getenv('INPUT_FOLDER')} folder")
    empty_folder(getenv("INPUT_FOLDER"))
    logger.debug(f"Clearing {getenv('OUTPUT_FOLDER')} folder")
    empty_folder(getenv("OUTPUT_FOLDER"))
