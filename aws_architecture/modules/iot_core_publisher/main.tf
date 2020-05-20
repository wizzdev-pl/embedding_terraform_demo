# --------------------
# Iot Thing
# - create things
# - create certs
# - attach things to certs
# ---------------------


# ---------------------
# Iot Thing
resource "aws_iot_thing" "iot_thing" {
  name = each.key
  thing_type_name = aws_iot_thing_type.iot_thing_type.name
  for_each = var.thing_names
}

# ---------------------
# Iot Thing Type
resource "aws_iot_thing_type" "iot_thing_type" {
  name = var.thing_type_name
}

# ---------------------
# IoT Cert
resource "aws_iot_certificate" "iot_thing_cert" {
  for_each = var.thing_names
  active = true
}

# ---------------------
# Attach Cert to Thing
resource "aws_iot_thing_principal_attachment" "attach_cert" {
  principal = aws_iot_certificate.iot_thing_cert[each.key].arn
  thing = aws_iot_thing.iot_thing[each.key].name
  for_each = var.thing_names
}

# ---------------------
# Attach Policy To Cert
resource "aws_iot_policy_attachment" "attach_policy" {
  for_each = var.thing_names
  policy = aws_iot_policy.iot_connect_and_publish_to_topic.name
  target = aws_iot_certificate.iot_thing_cert[each.key].arn
}
