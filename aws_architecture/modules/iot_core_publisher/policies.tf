resource "aws_iot_policy" "iot_connect_and_publish_to_topic" {
  name = "tf_iot_connect_and_publish_to_topic"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iot:Publish",
        "iot:Subscribe",
        "iot:Connect",
        "iot:Receive"
      ],
   "Resource": "*"
    }
  ]
}
EOF
}