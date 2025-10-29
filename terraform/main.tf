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

# Test instances for Bachelor thesis - realistic SME scenarios
# 4 m6a instances (non-burstable) representing typical German SME workloads
# These instances validate the integrated Cost+CO2 monitoring approach
resource "aws_instance" "test_instances" {
  for_each = var.test_instance_count > 0 ? {
    # Scenario 1: Always-On Database (Baseline)
    # Represents critical infrastructure that cannot be stopped
    # Purpose: Baseline for comparison, validates 24/7 cost and carbon tracking
    "baseline-24x7" = {
      instance_type = "m6a.large"
      cpu_target    = "40%"
      schedule      = "24/7"
      purpose       = "Always-on baseline (critical database)"
    }

    # Scenario 2: Office-Hours Application
    # Represents business applications used only during work hours (Mo-Fr 8-18h)
    # Purpose: Demonstrates office-hours optimization potential (15-25% cost savings)
    "office-hours" = {
      instance_type = "m6a.large"
      cpu_target    = "60%"
      schedule      = "Mo-Fr 8-18h"
      purpose       = "Office-hours app (business hours only)"
    }

    # Scenario 3: Night Batch Processing
    # Represents batch jobs scheduled during low-carbon grid times (22-6h)
    # Purpose: Validates carbon-aware scheduling (15-35% CO2 reduction)
    "night-batch" = {
      instance_type = "m6a.large"
      cpu_target    = "80%"
      schedule      = "Daily 22-6h"
      purpose       = "Night batch job (carbon-aware candidate)"
    }

    # Scenario 4: Variable Workload
    # Represents dev/test environments with fluctuating load patterns
    # Purpose: Validates power consumption model with variable CPU utilization
    "variable-load" = {
      instance_type = "m6a.large"
      cpu_target    = "30-70% alternating"
      schedule      = "Daily 6-22h"
      purpose       = "Variable workload (dev/test environment)"
    }
  } : {}

  ami           = data.aws_ami.amazon_linux.id
  instance_type = each.value.instance_type
  monitoring    = var.enable_monitoring
  user_data     = file("${path.module}/user-data/${each.key}.sh")

  tags = merge(local.common_tags, {
    Name          = "${local.project_name}-${each.key}"
    CPUTarget     = each.value.cpu_target
    Schedule      = each.value.schedule
    Purpose       = each.value.purpose
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
