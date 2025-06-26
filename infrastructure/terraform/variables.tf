variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-central-1"
}

variable "aws_account_id" {
  description = "AWS Account ID where resources will be created"
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