terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

# Auto-generate project name if not provided
locals {
  # Use provided account ID or empty string for now
  account_id = var.aws_account_id

  # Generate project name from AWS account ID if not provided
  generated_project_name = var.aws_account_id != "" ? "carbon-finops-${substr(var.aws_account_id, -6, -1)}" : "carbon-finops-thesis"
  project_name           = var.project_name != "" ? var.project_name : local.generated_project_name

  # Common tags for all resources
  common_tags = {
    Project     = local.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    CreatedBy   = "CarbonAware-FinOps-Tool"
  }
}

# Data source to get current AWS account information (after provider is configured)
data "aws_caller_identity" "current" {}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  # Specific AWS Account (will be enforced via Makefile or terraform.tfvars)
  allowed_account_ids = var.aws_account_id != "" ? [var.aws_account_id] : null

  default_tags {
    tags = local.common_tags
  }
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}



# DynamoDB removed - Dashboard uses real-time API data directly
# This simplifies the architecture and reduces costs while maintaining data freshness


# Get the latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# Test instances for Bachelor thesis - CPU load scenarios
# 4 m6a instances (non-burstable) with varying CPU utilization levels
# These instances validate the power consumption model and CO2 impact correlation
resource "aws_instance" "test_instances" {
  for_each = var.test_instance_count > 0 ? {
    # Scenario 1: Low Load (40% CPU)
    # Validates baseline power consumption at low utilization
    "cpu-40pct" = {
      instance_type = "m6a.large"
      cpu_target    = "40%"
      workload_type = "Low-intensity baseline"
    }

    # Scenario 2: Medium Load (60% CPU)
    # Validates power consumption at moderate utilization
    "cpu-60pct" = {
      instance_type = "m6a.large"
      cpu_target    = "60%"
      workload_type = "Medium-intensity workload"
    }

    # Scenario 3: High Load (80% CPU)
    # Validates power consumption at high utilization
    "cpu-80pct" = {
      instance_type = "m6a.large"
      cpu_target    = "80%"
      workload_type = "High-intensity compute"
    }

    # Scenario 4: Variable Load (30-70% CPU alternating)
    # Validates power consumption model under fluctuating utilization
    "cpu-variable" = {
      instance_type = "m6a.large"
      cpu_target    = "30-70%"
      workload_type = "Fluctuating workload pattern"
    }
  } : {}

  ami           = data.aws_ami.amazon_linux.id
  instance_type = each.value.instance_type
  monitoring    = var.enable_monitoring
  user_data     = file("${path.module}/user-data/${each.key}.sh")

  tags = merge(local.common_tags, {
    Name          = "${local.project_name}-${each.key}"
    CPUTarget     = each.value.cpu_target
    WorkloadType  = each.value.workload_type
    Scenario      = each.key
    TestInstance  = "true"
    Thesis        = "BA-CarbonAware-FinOps-2025"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Outputs
output "instance_ids" {
  description = "IDs of all test instances"
  value       = [for instance in aws_instance.test_instances : instance.id]
}

output "instances" {
  description = "Complete instance information"
  value = {
    for key, instance in aws_instance.test_instances : key => {
      id            = instance.id
      instance_type = instance.instance_type
      public_ip     = instance.public_ip
      private_ip    = instance.private_ip
    }
  }
}

# DynamoDB outputs removed - using direct API integration only
