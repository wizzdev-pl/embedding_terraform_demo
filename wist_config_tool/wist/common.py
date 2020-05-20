import os
import sys
import logging


_TERRAFORM_STR = "terraform"

_AWS_CONFIG = ".aws_config"


cfg = None  # ApplicationConfig


def _running_from_source():
    if getattr(sys, 'frozen', False):
        return False
    else:
        return True


def get_terraform_dir():
    if _running_from_source():
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), _TERRAFORM_STR)
    else:
        return os.path.join(sys._MEIPASS, _TERRAFORM_STR)


def get_aws_config_path():
    if _running_from_source():
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), _AWS_CONFIG)
    else:
        return os.path.join(sys._MEIPASS, _AWS_CONFIG)


class ApplicationConfig():
    def __init__(self):
        self.terraform_exec_path: str = _TERRAFORM_STR
        self.aws_config_file_path: str = _AWS_CONFIG


def setup_config(devel=False):
    global cfg
    cfg = ApplicationConfig()

    cfg.terraform_exec_path = os.path.join(get_terraform_dir(), _TERRAFORM_STR)
    cfg.aws_config_file_path = get_aws_config_path()

    os.environ["TF_IN_AUTOMATION"] = "1"  # this will prevent Terraform from producing too much output, or asking for input

def setup_logger(level=logging.INFO):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.getLogger(None).setLevel(level)