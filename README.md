# Embedding Terraform in custom application - demo

This is a demonstration of a simple CLI application called WIST (WizzDev's IoT Setup Tool) 
for configuration of AWS cloud based IoT sensors infrastructure.

Main functionality of the application:
- listing all devices existing in current IoT Core setup, 
- adding new device, along with new certificates generation,
- removing existing device

Generated certificates can be then used to configure any IoT sensor, and enable it to submit its data to AWS.


This repository accompanies the following blog on WizzDev's website:
https://wizzdev.pl/blog/embedding-terraform-in-custom-application/ 



## Prerequisites

- installed Python version >= 3.6 (64 bit) with paths for pip and python in PATH
- installed virtualenv for python:
    
        pip install virtualenv

You need to have a valid AWS account with full access to Amazon IoT services (that is AWS credentials assigned).
(Check how to generate AWS Access keys [here](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html#Using_CreateAccessKey))


## Running from source

- clone or download the repository from: https://github.com/wizzdev-pl/embedding_terraform_demo
- navigate to embedding_terraform_demo/
- create a virtual environment and activate it

        python3 -m venv venv
        source ./venv/bin/activate
        
- install requirements:

        pip install -r requirements.txt
    
-  run:
        
        python wist_config_tool/run_wist.py


## CLI Usage

*If running from source substitute "__wist__" with "__python run_wist.py__" (specifying correct path to run_wist.py file!)*

On the first run your AWS credentials must be configured: 

- to setup your AWS credentials run:
    
        wist setup_aws 
        
    and input desired infomation when asked.
        
- to list all IoT devices available in your AWS IoT Core:

        wist list_devices
        
- to add new device to AWS IoT Core:

        wist add_device --dev_name device_name
       
        
- to remove a device from AWS IoT Core:

        wist remove_device --dev_name device_name
        
- to copy certificate for a specific device, to some destination

        wist get_cert --dev_name device_name --dest_dir pat/to/destination/directory
        

        
**Note:** The first call to `wist add_device` or `remove_device` may take longer because of Terraform binary being installed, as well Terraform environment initialized.


Also in case new Terraform version is available it will be downloaded automatically.
        
  
 ## Building tool to an executable

- clone or download the repository from: https://github.com/wizzdev-pl/embedding_terraform_demo
- navigate to embedding_terraform_demo/
- create a virtual environment and activate it

        python3 -m venv venv
        source ./venv/bin/activate
        
- install requirements and pyinstaller:

        pip install -r requiremens.txt

        pip install pyinstaller
    
- run:
    
        pyinstaller wist_config_tool/wist.spec
    
- `/dist/wist` is the output directory in which `wist` executable will be found.

Mark that the whole `wist/` folder must be e.g. zipped and distributed that way

