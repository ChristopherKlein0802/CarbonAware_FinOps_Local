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
    Project       = local.project_name
    Environment   = var.environment
    ManagedBy     = "Terraform"
    AnalysisMode  = var.deployment_mode
    CreatedBy     = "CarbonAware-FinOps-Tool"
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

# VPC for instances (only created if needed for test instances)
resource "aws_vpc" "main" {
  count = var.deployment_mode == "testing" ? 1 : 0
  
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${local.project_name}-vpc"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main[0].id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# Public Subnet
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main[0].id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet"
  }
}

# Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main[0].id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

# Route Table Association
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Security Group
resource "aws_security_group" "main" {
  name        = "${var.project_name}-sg"
  description = "Security group for Carbon-Aware FinOps test instances"
  vpc_id      = aws_vpc.main[0].id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-sg"
  }
}

# IAM Role for EC2 instances
resource "aws_iam_role" "ec2_role" {
  name = "${var.project_name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Role Policy
resource "aws_iam_role_policy" "ec2_policy" {
  name = "${var.project_name}-ec2-policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics",
          "ec2:DescribeTags"
        ]
        Resource = "*"
      }
    ]
  })
}

# Instance Profile
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# Lambda Execution Role
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Lambda Policy
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:StopInstances",
          "ec2:StartInstances",
          "ec2:DescribeTags"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ce:GetCostAndUsage",
          "ce:GetCostForecast"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Scan",
          "dynamodb:Query",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem"
        ]
        Resource = [
          aws_dynamodb_table.results.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "cloudwatch:GetMetricStatistics"
        ]
        Resource = "*"
      }
    ]
  })
}

# (Removed S3 bucket resources for minimal thesis setup)

# Single DynamoDB table for storing cost and carbon analysis results
resource "aws_dynamodb_table" "results" {
  name         = "${var.project_name}-results"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "instance_id"
  range_key    = "timestamp"

  attribute {
    name = "instance_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  tags = {
    Name = "${var.project_name}-results"
    Purpose = "Store cost and carbon analysis results"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "main" {
  name              = "/aws/${var.project_name}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-logs"
  }
}

# (Removed) test_instances module to keep infra minimal for thesis

# Four test instances with different scheduling patterns for thesis demonstration
# Only deployed in testing mode or when explicitly requested
resource "aws_instance" "test_instances" {
  for_each = var.deployment_mode == "testing" || var.test_instance_count > 0 ? {
    "baseline" = {
      schedule      = "24/7 Always Running"
      purpose       = "Baseline cost and carbon measurement"
      description   = "Always-on instance for establishing baseline costs and carbon emissions"
      instance_type = "t3.medium"  # Higher cost for significant baseline comparison
    }
    "office-hours" = {
      schedule      = "Office Hours Only (Mon-Fri 8-18)"
      purpose       = "Office hours scheduling demonstration"
      description   = "Runs only during business hours to demonstrate time-based optimization"
      instance_type = "t3.small"   # Medium cost for substantial office-hours savings
    }
    "weekdays-only" = {
      schedule      = "Weekdays Only (Mon-Fri 24h)"
      purpose       = "Weekend shutdown demonstration"
      description   = "Shuts down on weekends to demonstrate weekly scheduling patterns"
      instance_type = "t3.small"   # Medium cost for visible weekend savings
    }
    "carbon-aware" = {
      schedule      = "Carbon-Aware Scheduling"
      purpose       = "Carbon intensity based scheduling"
      description   = "Stops during high carbon intensity periods to minimize emissions"
      instance_type = "t3.micro"   # Lower cost but demonstrates carbon optimization focus
    }
  } : {}

  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = each.value.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.main.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  monitoring             = true

  tags = merge(local.common_tags, {
    Name         = "${local.project_name}-${each.key}"
    Schedule     = each.value.schedule
    Purpose      = each.value.purpose
    Description  = each.value.description
    InstanceRole = "TestInstance"
    ScheduleType = each.key
  })
}

# Data source for Amazon Linux AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# Output values
output "vpc_id" {
  value = aws_vpc.main[0].id
}

output "subnet_id" {
  value = aws_subnet.public.id
}

output "security_group_id" {
  value = aws_security_group.main.id
}

output "dynamodb_results_table" {
  value = aws_dynamodb_table.results.id
}

output "instance_ids" {
  value = [for instance in aws_instance.test_instances : instance.id]
}

output "instance_details" {
  value = {
    for key, instance in aws_instance.test_instances : key => {
      id          = instance.id
      schedule    = instance.tags.Schedule
      purpose     = instance.tags.Purpose
      private_ip  = instance.private_ip
    }
  }
}

output "lambda_role_arn" {
  value = aws_iam_role.lambda_role.arn
}
