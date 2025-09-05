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
  description = "AWS profile for authentication (supports SSO profiles)"
  type        = string
  default     = "default"
}

variable "project_name" {
  description = "Name of the project (will be auto-generated based on account if not provided)"
  type        = string
  default     = ""
}

variable "analyze_all_instances" {
  description = "Analyze ALL instances in the account (true) or only tagged test instances (false)"
  type        = bool
  default     = true
}

variable "deployment_mode" {
  description = "Deployment mode: 'universal' for any account, 'testing' for specific project instances"
  type        = string
  default     = "universal"
  
  validation {
    condition     = contains(["universal", "testing"], var.deployment_mode)
    error_message = "Deployment mode must be either 'universal' or 'testing'."
  }
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

# API Configuration Variables for secure credential management
variable "electricitymap_api_key" {
  description = "ElectricityMap API key (will be stored securely in SSM)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "watttime_username" {
  description = "WattTime API username (will be stored securely in SSM)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "watttime_password" {
  description = "WattTime API password (will be stored securely in SSM)"
  type        = string
  default     = ""
  sensitive   = true
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


variable "lambda_log_retention_days" {
  description = "CloudWatch Log retention in days for Lambda functions"
  type        = number
  default     = 7
}
