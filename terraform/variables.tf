variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-central-1"
}

variable "aws_account_id" {
  description = "AWS Account ID where resources will be created (optional - will auto-detect from SSO if not provided)"
  type        = string
  default     = ""
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


variable "environment" {
  description = "Environment name"
  type        = string
  default     = "development"
}

variable "test_instance_count" {
  description = "Number of test EC2 instances (optimized for thesis validation)"
  type        = number
  default     = 4
}

variable "enable_monitoring" {
  description = "Enable detailed monitoring"
  type        = bool
  default     = true
}
