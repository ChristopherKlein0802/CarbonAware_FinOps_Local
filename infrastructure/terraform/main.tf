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
  # Generate project name from AWS account ID if not provided
  generated_project_name = "carbon-finops-${substr(var.aws_account_id, -6, -1)}"
  project_name = var.project_name != "" ? var.project_name : local.generated_project_name
  
  # Common tags for all resources
  common_tags = {
    Project     = local.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    CreatedBy   = "CarbonAware-FinOps-Tool"
  }
}

provider "aws" {
  region = var.aws_region
  profile = var.aws_profile

  # Specific AWS Account (can be any account with proper SSO access)
  allowed_account_ids = [var.aws_account_id]
  
  default_tags {
    tags = local.common_tags
  }
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}



# DynamoDB table for storing analysis results and API data
resource "aws_dynamodb_table" "results" {
  name           = "${local.project_name}-analysis-data"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "PK"
  range_key      = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK" 
    type = "S"
  }

  # GSI for querying by data type
  global_secondary_index {
    name            = "DataTypeIndex"
    hash_key        = "DataType"
    range_key       = "Timestamp"
    projection_type = "ALL"
  }

  attribute {
    name = "DataType"
    type = "S"
  }

  attribute {
    name = "Timestamp"
    type = "S"
  }

  tags = {
    Name        = "${local.project_name}-analysis-data"
    Description = "Stores API data and analysis results for dashboard"
  }
}


# Get the latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# Extended test instances for comprehensive scheduling strategy analysis
# Multiple instances per size for statistical comparison + Enterprise scenario
resource "aws_instance" "test_instances" {
  for_each = var.test_instance_count > 0 ? {
    # Small instances - baseline comparison
    "baseline-small" = {
      schedule      = "Current: Always Running (Analysis Baseline)"
      purpose       = "Small baseline cost and carbon measurement"
      description   = "Small instance - shows current costs for analysis"
      instance_type = "t3.small"
    }
    "analysis-small" = {
      schedule      = "Current: Always Running (Carbon Analysis Target)"
      purpose       = "Small instance carbon optimization analysis"
      description   = "Small instance - analyzed for carbon scheduling potential"
      instance_type = "t3.small"
    }
    
    # Medium instances - core comparison (4x for statistical significance)
    "baseline-medium" = {
      schedule      = "Current: Always Running (Analysis Baseline)"
      purpose       = "Medium baseline for scheduling comparison"
      description   = "Medium instance - current costs baseline"
      instance_type = "t3.medium"
    }
    "office-target-medium" = {
      schedule      = "Current: Always Running (Office Hours Analysis)"
      purpose       = "Medium instance office hours potential analysis"
      description   = "Medium instance - analyzed for office hours scheduling"
      instance_type = "t3.medium"
    }
    "weekend-target-medium" = {
      schedule      = "Current: Always Running (Weekend Analysis)"
      purpose       = "Medium instance weekend shutdown potential"
      description   = "Medium instance - analyzed for weekend scheduling"
      instance_type = "t3.medium"
    }
    "carbon-target-medium" = {
      schedule      = "Current: Always Running (Carbon Analysis)"
      purpose       = "Medium instance carbon optimization potential"
      description   = "Medium instance - analyzed for carbon scheduling"
      instance_type = "t3.medium"
    }
    
    # Large instance - Enterprise scenario
    "enterprise-large" = {
      schedule      = "Current: Always Running (Enterprise Analysis)"
      purpose       = "Enterprise workload optimization analysis"
      description   = "Large instance - enterprise optimization potential"
      instance_type = "t3.large"
    }
    
    # Micro instance - IoT/Edge scenario
    "edge-micro" = {
      schedule      = "Current: Always Running (Edge Analysis)"
      purpose       = "Edge/IoT optimization analysis"
      description   = "Micro instance - edge computing optimization potential"
      instance_type = "t3.micro"
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
    AnalysisTarget = "true"
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

output "dynamodb_table_name" {
  description = "DynamoDB table name for analysis data"
  value = aws_dynamodb_table.results.name
}

output "dynamodb_table_arn" {
  description = "DynamoDB table ARN"
  value = aws_dynamodb_table.results.arn
}