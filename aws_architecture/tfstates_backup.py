import botocore.exceptions
import datetime
import argparse
import pathlib
import logging
import boto3
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
s3 = None


def init_aws_client():
    global s3
    s3 = boto3.client('s3')


BUCKET = "tfstates.backup"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', help="Time in minutes how long lock on tfstate file will work", default=30)
    parser.add_argument('--path', required=True, help="Path to tfstate file")
    parser.add_argument('--push', help="Upload tfstate file to S3", action='store_true')
    parser.add_argument('--pull', help="Download tfstate file backup from S3", action='store_true')
    parser.add_argument('--lock', help="Lock tfstate file", action='store_true')
    parser.add_argument('--unlock', help="Unlock tfstate file", action='store_true')
    parser.add_argument('--is_locked', help="Check if file is locked", action='store_true')
    parse_args.print_help = parser.print_help
    return parser.parse_args()


def _get_s3_name_and_s3_lock_name(file_path: str):
    this_file_path = pathlib.Path(__file__).resolve().absolute()
    state_file_path = pathlib.Path(file_path).resolve().absolute()
    this_file_path_dirname = os.path.dirname(this_file_path)
    this_project_parent_path, project_name = os.path.split(this_file_path_dirname)
    path_for_key = str(state_file_path)[len(this_project_parent_path)+1:]
    s3_name = "__".join(path_for_key.split("\\") if os.name == 'nt' else path_for_key.split('/'))
    return s3_name, s3_name + ".lock"


def lock(state_terraform_file_path: str):
    """ Lock tfstate file """
    s3_name, s3_lock_name = _get_s3_name_and_s3_lock_name(state_terraform_file_path)
    s3.put_object(Body=b'-', Bucket=BUCKET, Key=s3_lock_name)
    logging.info(f"Locked {s3_name} file")


def unlock(state_terraform_file_path: str):
    """ Unlock tfstate file """
    s3_name, s3_lock_name = _get_s3_name_and_s3_lock_name(state_terraform_file_path)
    s3.delete_object(Bucket=BUCKET, Key=s3_lock_name)
    logging.info(f"Unlocked {s3_name} file")


def is_locked(state_terraform_file_path: str, timeout=30):
    """ Check if tfstate file is locked or timeout passed """
    s3_name, s3_lock_name = _get_s3_name_and_s3_lock_name(state_terraform_file_path)
    try:
        tfstate_file_head = s3.head_object(Bucket=BUCKET, Key=s3_name)
        lock_file_head = s3.head_object(Bucket=BUCKET, Key=s3_lock_name)
    except botocore.exceptions.ClientError:
        logging.debug("Lock file doesn't exist")
        return False
    if lock_file_head['LastModified'] < tfstate_file_head['LastModified']:
        logging.debug("Lock file is older than tfstate file")
        return False
    lock_datetime_and_timeout = (lock_file_head['LastModified'] + datetime.timedelta(minutes=timeout)).replace(
        tzinfo=None)
    now_datetime = datetime.datetime.utcnow().replace(tzinfo=None)
    if lock_datetime_and_timeout < now_datetime:
        logging.debug("Timeout passed")
        return False
    return True


def pull(state_terraform_file_path: str):
    """ Download tfstate file backup from S3 """
    s3_name, s3_lock_name = _get_s3_name_and_s3_lock_name(state_terraform_file_path)
    file = s3.get_object(Bucket=BUCKET, Key=s3_name)
    with open(state_terraform_file_path, 'wb') as terraform_file:
        terraform_file.write(file['Body'].read())
    logging.info("Backup downloaded from AWS S3 without problems")


def push(state_terraform_file_path: str):
    """ Upload tfstate file to S3 """
    s3_name, s3_lock_name = _get_s3_name_and_s3_lock_name(state_terraform_file_path)
    with open(state_terraform_file_path, 'rb') as file_obj:
        try:
            s3.upload_fileobj(file_obj, Bucket=BUCKET, Key=s3_name)
            logging.info("Backup is safe on AWS S3")
        except:
            logging.exception("Backup upload fails")


if __name__ == '__main__':
    init_aws_client()
    args = parse_args()
    if args.push:
        logging.info("Uploading .tfstate file to S3")
        push(args.path)
    elif args.pull:
        logging.info("Downloading .tfstate backup from S3")
        pull(args.path)
    elif args.lock:
        logging.info("Creating lock on .tfstate backup from S3")
        lock(args.path)
    elif args.unlock:
        logging.info("Removing lock on .tfstate backup from S3")
        unlock(args.path)
    elif args.is_locked:
        if is_locked(args.path):
            logging.info(".tfstate file is locked")
        else:
            logging.info(".tfstate file isn't locked")
    else:
        parse_args.print_help()
