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
  project_name = var.project_name != "" ? var.project_name : local.generated_project_name

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
  region = var.aws_region
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

# Optimized test instances for Bachelor thesis validation
# 4 instances covering key scenarios with academic rigor and cost efficiency
resource "aws_instance" "test_instances" {
  for_each = var.test_instance_count > 0 ? {
    # Small instance - SME baseline scenario
    "sme-small" = {
      schedule      = "Current: Always Running (SME Analysis)"
      purpose       = "SME workload optimization analysis (baseline)"
      description   = "Small instance - SME office hours optimization potential"
      instance_type = "t3.small"
      scenario      = "SME Office Hours (60-72% savings potential)"
    }
    
    # Medium instance - Core business scenario  
    "business-medium" = {
      schedule      = "Current: Always Running (Business Analysis)"
      purpose       = "Core business workload carbon-aware optimization"
      description   = "Medium instance - primary carbon scheduling analysis"
      instance_type = "t3.medium" 
      scenario      = "Carbon-Aware Scheduling (15-35% CO2 reduction)"
    }
    
    # Large instance - Enterprise scenario
    "enterprise-large" = {
      schedule      = "Current: Always Running (Enterprise Analysis)"
      purpose       = "Enterprise workload comprehensive optimization"
      description   = "Large instance - multi-strategy optimization analysis"
      instance_type = "t3.large"
      scenario      = "Hybrid Strategy (Cost + Carbon optimization)"
    }
    
    # Micro instance - Edge/Cost-sensitive scenario
    "edge-micro" = {
      schedule      = "Current: Always Running (Edge Analysis)"
      purpose       = "Edge computing and cost-sensitive analysis"
      description   = "Micro instance - edge computing optimization validation"
      instance_type = "t3.micro"
      scenario      = "Weekend-Only (25-30% savings potential)"
    }
  } : {}

  ami           = data.aws_ami.amazon_linux.id
  instance_type = each.value.instance_type
  monitoring    = var.enable_monitoring

  tags = merge(local.common_tags, {
    Name         = "${local.project_name}-${each.key}"
    ScheduleType = each.key
    Purpose      = each.value.purpose
    Schedule     = each.value.schedule
    Description  = each.value.description
    Scenario     = each.value.scenario
    AnalysisTarget = "true"
    ThesisValidation = "Bachelor-2025"
    # Enhanced analytics tags
    BusinessSize = each.key == "sme-small" ? "SME" : each.key == "business-medium" ? "Business" : each.key == "enterprise-large" ? "Enterprise" : "Edge"
    OptimizationType = each.key == "sme-small" ? "OfficeHours" : each.key == "business-medium" ? "CarbonAware" : each.key == "enterprise-large" ? "Hybrid" : "WeekendOnly"
    PowerConsumption = each.value.instance_type == "t3.micro" ? "8.2W" : each.value.instance_type == "t3.small" ? "10.7W" : each.value.instance_type == "t3.medium" ? "11.5W" : "18.4W"
    ResearchFocus = "German-SME-CarbonAware-FinOps"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Outputs
output "instance_ids" {
  description = "IDs of all test instances"
  value = [for instance in aws_instance.test_instances : instance.id]
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