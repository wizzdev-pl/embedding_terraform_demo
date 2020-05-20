import subprocess
import logging
import importlib
import os


def check_environment():
    assert subprocess.check_output(['which', 'terraform'])
    boto3 = importlib.import_module('boto3')
    botocore = importlib.import_module('botocore')


def check_aws():
    import boto3
    assert boto3.client('sts').get_caller_identity()
    assert boto3.client('s3').head_bucket(Bucket='tfstates.backup')


def prepare_dirs_structure():
    data_dir = os.path.join(os.getcwd(), 'data')
    if not os.path.isdir(data_dir):
        logging.debug(f"Create dir for data under path {data_dir}")
        os.mkdir(data_dir)


def create_needed_files():
    things_file = os.path.join(os.getcwd(), 'data', 'things.json')
    if not os.path.isfile(things_file):
        with open(things_file, 'w') as file:
            logging.debug(f"Create thins registry under path {things_file}")
            file.write('[]')


def initialize_aws_architecture():
    # Tests
    logging.info("Check if all needed binaries are installed")
    try:
        check_environment()
    except Exception:
        logging.exception("Error occurred while checking environment")
        raise Exception("Initialization failed")

    logging.info("Check if AWS is configured properly")
    try:
        check_environment()
    except Exception:
        logging.exception("Error occurred while checking aws configuration")
        raise Exception("Initialization failed")

    # Prepare env
    prepare_dirs_structure()
    create_needed_files()

    # End
    logging.info("AWS Architecture initialized with success")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    initialize_aws_architecture()
