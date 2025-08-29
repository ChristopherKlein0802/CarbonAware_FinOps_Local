variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-central-1"
}

variable "aws_account_id" {
  description = "AWS Account ID where resources will be created"
  type        = string
}

variable "aws_profile"  {
  description = "AWS profile for authentication"
  type        = string
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "carbon-aware-finops"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "development"
}

variable "test_instance_count" {
  description = "Number of test EC2 instances"
  type        = number
  default     = 4
}

variable "instance_type" {
  description = "EC2 instance type for testing"
  type        = string
  default     = "t3.micro"  # Changed to micro for cost savings
}

variable "enable_monitoring" {
  description = "Enable detailed monitoring"
  type        = bool
  default     = true
}

variable "carbon_api_provider" {
  description = "Carbon intensity API provider"
  type        = string
  default     = "electricitymap"
  
  validation {
    condition     = contains(["watttime", "electricitymap"], var.carbon_api_provider)
    error_message = "Carbon API provider must be either 'watttime' or 'electricitymap'."
  }
}
# Lambda-spezifische Variablen
variable "electricitymap_api_key" {
  description = "ElectricityMap API Key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "watttime_username" {
  description = "WattTime API Username"
  type        = string
  default     = ""
  sensitive   = true
}

variable "watttime_password" {
  description = "WattTime API Password"
  type        = string
  default     = ""
  sensitive   = true
}

variable "notification_email" {
  description = "Email address for notifications"
  type        = string
  default     = "ch.klein@reply.de"
}

variable "enable_lambda_functions" {
  description = "Enable Lambda functions deployment"
  type        = bool
  default     = false
}

variable "lambda_log_retention_days" {
  description = "CloudWatch Log retention in days for Lambda functions"
  type        = number
  default     = 7
}
