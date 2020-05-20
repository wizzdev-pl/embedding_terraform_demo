import os
import stat
import re
import sys
import subprocess
import requests
import logging
import hashlib
import zipfile

import wist.common as common
from wist.common import get_terraform_dir


# this could be used if someone have time to "reverse engineer" Hashicorp's checkpoint-api
# def get_latest_terraform_verison():
#     conn = http.client.HTTPConnection('checkpoint-api.hashicorp.com')
#     conn.request("GET", "/ve/check/Terraform")

_DEFAULT_TERRAFORM_VERSION_TO_DOWNLOAD = "0.12.24"


def _download_terraform_zip(version: str):

    archive_name = _get_archive_name_for_current_platform(version)

    full_url = f"https://releases.hashicorp.com/terraform/{version}/{archive_name}"

    logging.info(f'Downloading Terraform v{version} from: {full_url}. This may take some time...')

    response = requests.get(full_url, stream=True)
    response.raise_for_status()

    with open(archive_name, "wb") as handle:
        for data in response.iter_content(chunk_size=8*1024):
            if data:
                handle.write(data)

    if not (_check_zip_sha256(version, archive_name)):
        raise Exception(f'Sha256 of downloaded file is incorrect!')

    return archive_name


def _get_archive_name_for_current_platform(version: str):
    system = ''
    if sys.platform.startswith('win32'):
        system = 'windows'
    elif sys.platform.startswith('linux'):
        system = 'linux'
    elif sys.platform.startswith('darwin'):
        system = 'darwin'
    else:
        print('Platform not supported!')

    arch = 'amd64' if (sys.maxsize > 2 ** 32) else '386'

    return f'terraform_{version}_{system}_{arch}.zip'


def _compute_sha256_sum(filename: str):
    sha256_hash = hashlib.sha256()
    with open(filename, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def _check_zip_sha256(version: str, zip_file_name: str):

    sha_sums_file = f"terraform_{version}_SHA256SUMS"
    sha_url = f"https://releases.hashicorp.com/terraform/{version}/{sha_sums_file}"
    r_sha = requests.get(sha_url)
    r_sha.raise_for_status()

    sha_keys = r_sha.content.decode('utf-8')
    for line in sha_keys.split('\n'):
        key, file = line.split(' ', 1)
        if file.lstrip(' ') == zip_file_name:
            break

    computed_hash = _compute_sha256_sum(zip_file_name)

    return bool(computed_hash == key)


def get_terraform(version: str):
    if version is None:
        version=_DEFAULT_TERRAFORM_VERSION_TO_DOWNLOAD

    new_terraform_archive_file = _download_terraform_zip(version)

    with zipfile.ZipFile(new_terraform_archive_file, 'r') as zip_ref:
        zip_ref.extractall(get_terraform_dir())

    # add permissions to execute
    if sys.platform.startswith('linux'):
        os.chmod(common.cfg.terraform_exec_path, 0o777)


def check_tf_latest_version():

    """ This function assumes the following output to 'terraform version' command in case a newer version is available:
        > terraform version
        Terraform v0.12.23

        Your version of Terraform is out of date! The latest version
        is 0.12.24. You can update by downloading from https://www.terraform.io/downloads.html

    There are probably no guarantees that this form of the output will remain unchanged always,
    there is another option to consider version checking - through Hashicorp checkpoint api, but it is not officially open.

    :return:
    True, current_version - if current version is up to date
    False, latest_version - if current version is out of date
    False, None           - if no Terraform version found (not installed)
    """

    try:
        result = subprocess.run([common.cfg.terraform_exec_path, 'version'], stdout=subprocess.PIPE)

    except FileNotFoundError:
        logging.warning('Terraform not installed')
        return False, None

    else:

        if 'out of date' in result.stdout.decode('utf-8'):
            result_str = result.stdout.decode('utf-8')
            first_line, rest = result_str.split('\n', 1)

            _, current_tf_version = first_line.split(' ')
            current_tf_version = current_tf_version.lstrip('v')

            newest_version = re.findall("\d*\.\d+\.\d+", rest)[-1]  # because of aws backed version that may appear in the output as well

            logging.info(f'Discovered installed Terraform v{current_tf_version} but newest version {newest_version} will be downloaded...')

            return False, newest_version

        else:

            result_str = result.stdout.decode('utf-8')
            first_line, rest = result_str.split('\n', 1)
            _, tf_version = first_line.split(' ', 1)
            tf_version = tf_version.lstrip('v')
            logging.info(f'Using Terraform {tf_version} which is up to date.')

            return True, tf_version



if __name__ == '__main__':
    import time
    from wist.common import setup_config
    logging.getLogger(None).setLevel(logging.INFO)
    setup_config(devel=True)

    time1 = time.time()
    ver = "0.12.23"

    print(check_tf_latest_version())
    #get_terraform(ver)
    print(f'Took : {time.time()-time1}')


