import argparse
import logging
import json
import shutil
import time
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DEVICES_FILE = os.path.join(DATA_DIR, 'things.json')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--add')
    parser.add_argument('--remove')
    parser.add_argument('--show', action='store_true')
    parser.add_argument('--get-certs', metavar="STATE_FILE_PATH")
    parser.add_argument('--get-things-from-state', metavar="STATE_FILE_PATH")
    parse_args.print_help = parser.print_help
    return parser.parse_args()


def add_device(device_name):
    with open(DEVICES_FILE, 'r') as devices_file:
        devices = json.load(devices_file)  # type: list
    #devices = list(set(devices + [device_name]))
    if device_name in devices:
        logging.info(f'Device with name {device_name} already exists in devices registry! Not changing anything.')
    else:
        devices.append(device_name)
        with open(DEVICES_FILE, 'w') as devices_file:
            json.dump(devices, devices_file)
        logging.info(f"Added [{device_name}] to devices registry")


def remove_device(device_name):
    with open(DEVICES_FILE, 'r') as devices_file:
        devices = json.load(devices_file)  # type: list
    if device_name in devices:
        devices.remove(device_name)
        with open(DEVICES_FILE, 'w') as devices_file:
            json.dump(devices, devices_file)
        logging.info(f"Removed [{device_name}] from devices registry")
    else:
        logging.warning(f"There is no device with such name: [{device_name}]")


def get_devices():
    with open(DEVICES_FILE, 'r') as devices_file:
        devices = json.load(devices_file)  # type: list
    return devices

def show_devices():
    devices = get_devices()
    for i, device in enumerate(devices):
        print(i + 1, device)

def extract_certs_from_state_file(state_file_path):
    devices_dir = os.path.join(DATA_DIR, 'iot_certs')
    last_read_file = os.path.join(devices_dir, '.read')

    if os.path.isfile(last_read_file) and os.stat(last_read_file).st_mtime_ns > os.stat(state_file_path).st_mtime_ns:
        return

    if os.path.isdir(devices_dir):
        shutil.rmtree(devices_dir, ignore_errors=True)
    os.mkdir(devices_dir)

    with open(state_file_path, 'r') as file:
        state_file_data = json.load(file)

        devices_entry = [entry for entry in state_file_data['resources'] if entry['type'] == 'aws_iot_thing']
        if not devices_entry:
            logging.error("Cannot get certs. There are no devices blocks")
            return

        certs_entry = [entry for entry in state_file_data['resources'] if entry['type'] == 'aws_iot_certificate']
        if not certs_entry:
            logging.error("Cannot get certs. There are no certs blocks")
            return

        devices = devices_entry[0]['instances']
        certs = certs_entry[0]['instances']

        if len(devices) != len(certs):
            logging.error("Cannot get certs. Amount of devices isn't equal to amount of certs.")

        for i, device in enumerate(devices):
            device_dir_path = os.path.join(devices_dir, device['attributes']['name'])
            if not os.path.isdir(device_dir_path):
                os.mkdir(device_dir_path)
            for key in ['certificate_pem', 'private_key', 'public_key']:
                with open(os.path.join(device_dir_path, key), 'w') as cert_file:
                    cert_file.write(certs[i]['attributes'][key])

    with open(last_read_file, 'w') as last_read:
        last_read.write(str(time.time()))


def extract_things_from_state_file(state_file_path):
    with open(state_file_path, 'r') as file:
        state_file_data = json.load(file)

        devices_entry = [entry for entry in state_file_data['resources'] if entry['type'] == 'aws_iot_thing']
        if not devices_entry:
            logging.error("Cannot get things. There is no devices blocks")
            return

        devices = devices_entry[0]['instances']
        devices_names = []
        for device in devices:
            devices_names.append(device['attributes']['name'])

        with open(os.path.join(DATA_DIR, 'things.json'), 'w') as things_registry_file:
            json.dump(devices_names, things_registry_file)


if __name__ == '__main__':
    args = parse_args()
    if args.add:
        logging.info("Adding device to registry")
        add_device(args.add)
    elif args.remove:
        logging.info("Removing device from registry")
        remove_device(args.remove)
    elif args.show:
        logging.info("Showing list of devices from registry")
        show_devices()
    elif args.get_certs:
        logging.info("Extracting certs files from state file")
        extract_certs_from_state_file(args.get_certs)
    elif args.get_things_from_state:
        logging.info("Extracting things from state file")
        extract_things_from_state_file(args.get_things_from_state)
    else:
        parse_args.print_help()
