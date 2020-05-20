import os
import json

import wist.common as common


def save_aws_config(aws_config: dict):
    with open(common.cfg.aws_config_file_path, 'w') as file:
        file.write(json.dumps(aws_config))


def aws_credentials_available():
    return os.path.exists(common.cfg.aws_config_file_path)


def setup_aws_credentials(access_key_id, secret_access_key, default_region):
    # this must  be called BEFORE importing any aws_architecture function!
    os.environ['AWS_ACCESS_KEY_ID'] = access_key_id
    os.environ['AWS_SECRET_ACCESS_KEY'] = secret_access_key
    os.environ['AWS_DEFAULT_REGION'] = default_region


def read_aws_credentials():
    # this must be called before any module from aws_tools is imported!
    with open(common.cfg.aws_config_file_path, 'r') as file:
        aws_config = json.loads(file.read())

    setup_aws_credentials(access_key_id = aws_config['access_key_id'],
                          secret_access_key=aws_config['secret_access_key'],
                          default_region=aws_config['default_region'])