import os
import sys
import shutil
import logging
import subprocess
import requests

from wist.common import _running_from_source
import wist.common as common
from wist.terraform_management import check_tf_latest_version
from wist.terraform_management import get_terraform

from aws_architecture import manage_thing
import aws_architecture.tfstates_backup as tfb


AWS_ROOT_CA_CERTIFICATE_URL = "https://www.amazontrust.com/repository/AmazonRootCA1.pem"

_TERRAFORM_STATE_FILE_NAME = 'terraform.tfstate'
_this_file_path = os.path.dirname(os.path.abspath(__file__))

if _running_from_source():
    _TERRAFORM_STATE_LOCAL_DIR = os.path.join(_this_file_path, '..', '..', 'aws_architecture', 'environments', 'things_management')
    AWS_CERTS_DIRECTORY = os.path.join(_this_file_path, '..', '..', 'aws_architecture', 'data', 'iot_certs')

else:
    _TERRAFORM_STATE_LOCAL_DIR = os.path.join(sys._MEIPASS, 'aws_architecture', 'environments', 'things_management')
    AWS_CERTS_DIRECTORY = os.path.join(sys._MEIPASS, 'aws_architecture', 'data', 'iot_certs')

TERRAFORM_STATE_FILE_PATH_LOCAL = os.path.join(_TERRAFORM_STATE_LOCAL_DIR, _TERRAFORM_STATE_FILE_NAME)


class WrongAwsKeysError(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class NoInternetConnection(Exception):
    def __init__(self, *args):
        super().__init__(*args)


def init_aws_client():
    tfb.init_aws_client()


def get_all_available_aws_devices(download_backup=True) -> list:
    if download_backup:
        try:
            tfb.pull(TERRAFORM_STATE_FILE_PATH_LOCAL)
        except Exception as e:
            if 'InvalidAccessKeyId' in str(e):
                raise WrongAwsKeysError(f'Failed to pull file {TERRAFORM_STATE_FILE_PATH_LOCAL}') from e
            elif '' in str(e):
                raise NoInternetConnection(f'Failed to pull file {TERRAFORM_STATE_FILE_PATH_LOCAL}.') from e
            else:
                logging.error(f'Failed to pull file {TERRAFORM_STATE_FILE_PATH_LOCAL}. Reason: {str(e)}')
                raise Exception(f'Failed to update devices list. Reason: {str(e)}')
    manage_thing.extract_things_from_state_file(TERRAFORM_STATE_FILE_PATH_LOCAL)  # get json from state file
    devices = manage_thing.get_devices()
    return devices


def _is_terraform_initialized():
    if '.terraform' in os.listdir(_TERRAFORM_STATE_LOCAL_DIR):
        return True
    else:
        return False


def apply_changes_in_terraform(upload_backup=True):

    cwd = os.getcwd()
    os.chdir(_TERRAFORM_STATE_LOCAL_DIR)

    up_to_date = False
    while not up_to_date:
        # loop because first time can download older version
        up_to_date, version = check_tf_latest_version()
        if not up_to_date:
            get_terraform(version)

    if not _is_terraform_initialized():
        logging.info('Initializing Terraform environment...')
        rc = subprocess.call([common.cfg.terraform_exec_path, "init", "-input=false"])
        if rc != 0:
            raise Exception(f'Calling terraform init ended with an error: {rc}.')
        logging.info('Terraform environment initialized.')

    logging.info(f'Testing changes terraform (plan)...')
    my_env = os.environ.copy()
    rc = subprocess.call([common.cfg.terraform_exec_path, "plan", "-input=false"], env=my_env)
    if rc != 0:
        raise Exception(f'Calling terraform plan ended with an error: {rc}.')

    logging.info(f'Applying changes to terraform...')
    rc = subprocess.call([common.cfg.terraform_exec_path, "apply", "-auto-approve", "-input=false"])
    if rc != 0:
        raise Exception(f'Calling terraform apply ended with an error: {rc}.')

    if upload_backup:
        tfb.push(TERRAFORM_STATE_FILE_PATH_LOCAL)
        if tfb.is_locked(TERRAFORM_STATE_FILE_PATH_LOCAL):
            tfb.unlock(TERRAFORM_STATE_FILE_PATH_LOCAL)

    os.chdir(cwd)


def add_new_device_to_aws(device_name, download_backup=True):

    try:
        if download_backup:
            if tfb.is_locked(TERRAFORM_STATE_FILE_PATH_LOCAL):
                logging.error(f'Could not lock terraform backup state file!')
                return

            tfb.pull(TERRAFORM_STATE_FILE_PATH_LOCAL)
            tfb.lock(TERRAFORM_STATE_FILE_PATH_LOCAL)  # lock state file on cloud
            manage_thing.extract_things_from_state_file(TERRAFORM_STATE_FILE_PATH_LOCAL)  # get json from state file
        manage_thing.add_device(device_name)

        apply_changes_in_terraform()

        manage_thing.extract_certs_from_state_file(TERRAFORM_STATE_FILE_PATH_LOCAL)

        # some additional action can be taken here e.g. registering device in DynamoDB

    except Exception as e:
        tfb.unlock(TERRAFORM_STATE_FILE_PATH_LOCAL)
        logging.error(f'Adding new device to AWS failed. Reason: {str(e)}')
        raise Exception(f'Adding new device to AWS failed. Reason: {str(e)}')

    else:
        logging.info(f'Device {device_name} added successfully!')


def delete_device_from_aws(device_name, download_backup=True):
    try:
        if download_backup:
            if tfb.is_locked(TERRAFORM_STATE_FILE_PATH_LOCAL):
                logging.error(f'Could not lock terraform backup state file!')
                return

            tfb.pull(TERRAFORM_STATE_FILE_PATH_LOCAL)
            tfb.lock(TERRAFORM_STATE_FILE_PATH_LOCAL)  # lock state file on cloud
        manage_thing.extract_things_from_state_file(TERRAFORM_STATE_FILE_PATH_LOCAL)  # get json from state file
        manage_thing.remove_device(device_name)

        apply_changes_in_terraform()

        manage_thing.extract_certs_from_state_file(TERRAFORM_STATE_FILE_PATH_LOCAL)

    except Exception as e:
        tfb.unlock(TERRAFORM_STATE_FILE_PATH_LOCAL)
        logging.error(f'Removing device {device_name} from AWS failed. Reason: {str(e)}')
        raise Exception(f'Removing device {device_name} from AWS failed. Reason: {str(e)}')
    else:
        logging.info(f'Device {device_name} removed successfully!')


def copy_device_certs_to(device_name: str, dest_dir: str):
    try:
        tfb.pull(TERRAFORM_STATE_FILE_PATH_LOCAL)
    except Exception as e:
        logging.error(f'Failed to pull file {TERRAFORM_STATE_FILE_PATH_LOCAL}. Reason: {str(e)}')
        return

    manage_thing.extract_certs_from_state_file(TERRAFORM_STATE_FILE_PATH_LOCAL)  # get json from state file

    device_cert_dir = os.path.join(AWS_CERTS_DIRECTORY, device_name)
    if not os.path.isdir(device_cert_dir):
        raise Exception(f'Certificates for a specified device not created!')
    else:
        logging.info(f'Extracted certificate for {device_name}.')

    if not os.path.isdir(dest_dir):
        os.mkdir(dest_dir)

    shutil.copyfile(os.path.join(device_cert_dir, 'certificate_pem'), os.path.join(dest_dir, 'cert.crt'))
    logging.info(f'{device_name} certificate copied to "{dest_dir}/cert.crt".')

    shutil.copyfile(os.path.join(device_cert_dir, 'private_key'), os.path.join(dest_dir, 'priv.key'))
    logging.info(f'{device_name} private key copied to "{dest_dir}/priv.key".')

    # download amazon root ca
    logging.info(f'Donloading Amazon root CA to "{dest_dir}/cacert.pem"')
    ca_dest_path = os.path.join(dest_dir, 'cacert.pem')

    response = requests.get(AWS_ROOT_CA_CERTIFICATE_URL)
    response.raise_for_status()

    with open(ca_dest_path, "w") as file:
        file.write(response.content.decode('utf-8'))


def get_device_cert(device_name: str):
    manage_thing.extract_certs_from_state_file(TERRAFORM_STATE_FILE_PATH_LOCAL)  # get json from state file

    device_cert_dir = os.path.join(AWS_CERTS_DIRECTORY, device_name)
    if not os.path.isdir(device_cert_dir):
        raise Exception(f'Certificates for a specified device not created!')

    cert_path = os.path.join(device_cert_dir, 'certificate_pem')

    with open(cert_path, 'r') as file:
        device_cert = file.read()

    return device_cert


def get_device_priv_key(device_name: str):
    manage_thing.extract_certs_from_state_file(TERRAFORM_STATE_FILE_PATH_LOCAL)  # get json from state file

    device_cert_dir = os.path.join(AWS_CERTS_DIRECTORY, device_name)
    if not os.path.isdir(device_cert_dir):
        raise Exception(f'Certificates for a specified device not created!')

    key_path = os.path.join(device_cert_dir, 'private_key')

    with open(key_path, 'r') as file:
        device_key = file.read()

    return device_key


def untrack_device_from_terraform(device_name):
    devices = get_all_available_aws_devices()
    dev_key = None
    for key, name in enumerate(devices):
        if name == device_name:
            dev_key = key
            break

    # because Terraform documentation does not mention any DIR parameter in "terraform state" command,
    # we are assuming the need to change current dir for this:
    cwd = os.getcwd()
    os.chdir(_TERRAFORM_STATE_LOCAL_DIR)
    cmd = [common.cfg.terraform_exec_path, "state", "rm", f"module.iot_core_publisher.aws_iot_thing.iot_thing[{dev_key}]"]
    logging.info(f"Calling: {' '.join(cmd)}")
    rc = subprocess.call(cmd)
    if rc != 0:
        raise Exception(f'Calling terraform state rm ended with an error: {rc}.')

    manage_thing.extract_things_from_state_file(TERRAFORM_STATE_FILE_PATH_LOCAL)  # get json from state file
    tfb.push(TERRAFORM_STATE_FILE_PATH_LOCAL)
    if tfb.is_locked(TERRAFORM_STATE_FILE_PATH_LOCAL):
        tfb.unlock(TERRAFORM_STATE_FILE_PATH_LOCAL)

    os.chdir(cwd)
