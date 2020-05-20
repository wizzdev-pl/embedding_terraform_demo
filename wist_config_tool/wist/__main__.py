import os
import sys
import enum
import json
import time
import logging
import argparse


from wist import _version
from wist.common import setup_config, setup_logger
from wist.aws_credentials import save_aws_config, aws_credentials_available, read_aws_credentials
from wist.aws_tools import init_aws_client

_PROGRAM_NAME = "wist"

_DEFAULT_AWS_REGION = 'eu-west-2'



class RecognizedCommands(enum.Enum):
    SETUP_AWS = enum.auto()
    LIST_DEVICES = enum.auto()
    ADD_DEVICE = enum.auto()
    REMOVE_DEVICE = enum.auto()
    GET_CERT = enum.auto()


_commands_help = {RecognizedCommands.SETUP_AWS: "Setup your AWS credentials",
                  RecognizedCommands.LIST_DEVICES: "List all devices existing in your AWS IoT service",
                  RecognizedCommands.ADD_DEVICE: "Add new device to your AWS IoT service. All required certificates for that device will be created, and permissions granted",
                  RecognizedCommands.REMOVE_DEVICE: "Remove specified device from your AWS IoT service",
                  RecognizedCommands.GET_CERT: "Get certificate and keys for a specified device id, and copy them to output directory",
                  }


_commands_with_no_additional_parameters = {RecognizedCommands.LIST_DEVICES, RecognizedCommands.SETUP_AWS}   # set!
_commands_with_additional_parameters = set(RecognizedCommands).difference(_commands_with_no_additional_parameters)

_commands_with_device_name_arg = {RecognizedCommands.ADD_DEVICE, RecognizedCommands.REMOVE_DEVICE, RecognizedCommands.GET_CERT}




def parse_command_line_arguments():
    parser = argparse.ArgumentParser(_PROGRAM_NAME)

    parser.add_argument('-V', '--version', action='version', version='WIST version {}'.format(_version.__version__))

    commands_parser = parser.add_subparsers(title='COMMANDS', metavar='COMMAND [ARGS]', dest='subcommand')

    for command_name, command in RecognizedCommands.__members__.items():
        subparser = commands_parser.add_parser(command_name.lower(), help=_commands_help[command])
        if command in _commands_with_device_name_arg:
            subparser.add_argument("--dev_name", nargs=1, help="Device name", type=str, required=True)
        if command == RecognizedCommands.GET_CERT:
            subparser.add_argument("--dest_dir", nargs=1, help="Destination directory for certificate and key files.",
                                   type=str, required=True)

    parsed_args = parser.parse_args()
    if parsed_args.subcommand is None:
        parser.print_help()
        sys.exit(2)

    return parsed_args


def get_aws_config():
    print('Setting up AWS configuration')

    aws_config = {}
    aws_config['access_key_id'] = input(f'Input your AWS Access ID: ')
    aws_config['secret_access_key'] = input(f'Input your AWS Secret Acces Key: ')
    aws_config['default_region'] = input(f'Input your AWS region (default: {_DEFAULT_AWS_REGION}): ')
    aws_config['default_region'] = aws_config['default_region'] if aws_config['default_region'] else _DEFAULT_AWS_REGION

    save_aws_config(aws_config)

    logging.info(f'AWS config save successfully!')


def main():

    setup_config()
    setup_logger()

    init_aws_client()

    try:

        args = parse_command_line_arguments()

        if args.subcommand == RecognizedCommands.SETUP_AWS.name.lower():
            logging.info('Setup AWS')
            get_aws_config()

        elif not aws_credentials_available():
            # check if credntials exists if not - exit with info!
            logging.info("AWS credentials not set up! Please run 'wist setup_aws' first.")
            os._exit(1)

        read_aws_credentials()

        if args.subcommand == RecognizedCommands.LIST_DEVICES.name.lower():
            logging.info('List devices')
            from wist.aws_tools import get_all_available_aws_devices

            devices_list = get_all_available_aws_devices()
            for lp, device in enumerate(devices_list):
                print(f'{lp}: {device}')

        elif args.subcommand == RecognizedCommands.ADD_DEVICE.name.lower():
            device_name = args.dev_name[0]
            logging.info(f'Adding device {device_name}')

            from wist.aws_tools import add_new_device_to_aws

            add_new_device_to_aws(device_name)

        elif args.subcommand == RecognizedCommands.REMOVE_DEVICE.name.lower():
            device_name = args.dev_name[0]
            logging.info(f"Removing device {device_name}")

            from wist.aws_tools import delete_device_from_aws

            delete_device_from_aws(device_name)

        elif args.subcommand == RecognizedCommands.GET_CERT.name.lower():
            logging.info("Copying certificates")
            device_name = args.dev_name[0]
            dest_dir = args.dest_dir[0]

            from wist.aws_tools import copy_device_certs_to

            copy_device_certs_to(device_name, dest_dir)

        '''
        Another command can be added here to configure your IoT device using this tool (along with generating certificates etc)
        The implementation will depend on the manner in which the credentials should be downloaded to the device
        eg. along with the firmware or when connected via Wifi or Bluetooth in some configuration mode
        '''

        logging.info('Program finished')
        os._exit(0)

    except Exception as e:
        msg = f'Error! during program start: "{e}"'
        logging.exception(msg)
        os._exit(1)


if __name__ == '__main__':
    main()
