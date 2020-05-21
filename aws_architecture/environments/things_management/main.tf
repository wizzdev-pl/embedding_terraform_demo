provider "aws" {
  region = "eu-west-2"
}


module "iot_core_publisher" {
  source = "../../modules/iot_core_publisher"
  thing_names = jsondecode(file("../../data/things.json"))
  thing_type_name = "tf_wizzdev_iot_project"
}
