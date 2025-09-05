# SSM Parameters for secure API key storage
resource "aws_ssm_parameter" "electricitymap_api_key" {
  count = var.electricitymap_api_key != "" ? 1 : 0
  
  name  = "/${local.project_name}/electricitymap/api-key"
  type  = "SecureString"
  value = var.electricitymap_api_key
  
  tags = local.common_tags
}

resource "aws_ssm_parameter" "watttime_username" {
  count = var.watttime_username != "" ? 1 : 0
  
  name  = "/${local.project_name}/watttime/username"
  type  = "SecureString"
  value = var.watttime_username
  
  tags = local.common_tags
}

resource "aws_ssm_parameter" "watttime_password" {
  count = var.watttime_password != "" ? 1 : 0
  
  name  = "/${local.project_name}/watttime/password"
  type  = "SecureString"
  value = var.watttime_password
  
  tags = local.common_tags
}