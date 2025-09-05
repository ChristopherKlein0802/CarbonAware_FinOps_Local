#!/bin/bash
# Universal Deployment Script for Carbon-Aware FinOps Tool
# Supports SSO login and deployment to any AWS account

set -e

echo "🌱 Carbon-Aware FinOps - Universal Deployment"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values (German-focused)
AWS_PROFILE=${AWS_PROFILE:-"default"}
AWS_REGION=${AWS_REGION:-"eu-central-1"}  # Frankfurt - primary German region
DEPLOYMENT_MODE="universal"

# German regions validation
GERMAN_REGIONS=("eu-central-1" "eu-central-2")
if [[ ! " ${GERMAN_REGIONS[@]} " =~ " ${AWS_REGION} " ]]; then
    echo -e "${YELLOW}⚠️  Warning: Region $AWS_REGION is not a German region${NC}"
    echo "For best carbon data accuracy, consider using:"
    echo "  • eu-central-1 (Frankfurt) - Recommended"
    echo "  • eu-central-2 (Zurich)"
    echo ""
fi

echo -e "${BLUE}📋 Configuration:${NC}"
echo "  AWS Profile: $AWS_PROFILE"
echo "  AWS Region: $AWS_REGION"
echo "  Deployment Mode: $DEPLOYMENT_MODE"
echo ""

# Check if AWS CLI is configured
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install AWS CLI first.${NC}"
    exit 1
fi

# Get AWS account ID and check authentication
echo -e "${YELLOW}🔐 Checking AWS authentication...${NC}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query 'Account' --output text 2>/dev/null || echo "")

if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}❌ AWS authentication failed. Please check your profile and SSO login.${NC}"
    echo ""
    echo "For SSO users, run:"
    echo "  aws sso login --profile $AWS_PROFILE"
    echo ""
    echo "For regular AWS credentials, run:"
    echo "  aws configure --profile $AWS_PROFILE"
    exit 1
fi

echo -e "${GREEN}✅ AWS authentication successful${NC}"
echo "  Account ID: $AWS_ACCOUNT_ID"
echo "  Profile: $AWS_PROFILE"
echo "  Region: $AWS_REGION"

# Auto-generate project name based on account ID
PROJECT_NAME="carbon-finops-$(echo $AWS_ACCOUNT_ID | tail -c 7)"
echo "  Generated Project Name: $PROJECT_NAME"
echo ""

# Check if ElectricityMap API key is provided
if [ -z "$ELECTRICITYMAP_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  ELECTRICITYMAP_API_KEY environment variable not set${NC}"
    echo "The tool will still deploy but carbon data may not be available."
    echo "Set your API key with: export ELECTRICITYMAP_API_KEY=your-key-here"
    ELECTRICITYMAP_API_KEY=""
fi

# Navigate to terraform directory
cd infrastructure/terraform

# Initialize Terraform
echo -e "${YELLOW}🏗️  Initializing Terraform...${NC}"
terraform init

# Create terraform.tfvars for universal deployment
cat > terraform.tfvars << EOF
# Universal Deployment Configuration
aws_account_id = "$AWS_ACCOUNT_ID"
aws_region = "$AWS_REGION"
aws_profile = "$AWS_PROFILE"
project_name = "$PROJECT_NAME"
deployment_mode = "universal"
analyze_all_instances = true
carbon_api_provider = "electricitymap"
electricitymap_api_key = "$ELECTRICITYMAP_API_KEY"
environment = "production"
EOF

echo -e "${GREEN}✅ Created terraform.tfvars for universal deployment${NC}"

# Build Lambda packages
echo -e "${YELLOW}📦 Building Lambda deployment packages...${NC}"
./build_lambda.sh

# Plan deployment
echo -e "${YELLOW}📋 Planning Terraform deployment...${NC}"
terraform plan

# Ask for confirmation
echo ""
read -p "🚀 Deploy to AWS account $AWS_ACCOUNT_ID in region $AWS_REGION? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}❌ Deployment cancelled${NC}"
    exit 0
fi

# Apply deployment
echo -e "${YELLOW}🚀 Deploying infrastructure...${NC}"
terraform apply -auto-approve

# Get outputs
LAMBDA_FUNCTION_NAME=$(terraform output -raw carbon_scheduler_function_name 2>/dev/null || echo "")
DYNAMODB_TABLE=$(terraform output -raw dynamodb_results_table 2>/dev/null || echo "")

echo ""
echo -e "${GREEN}🎉 Deployment successful!${NC}"
echo "=============================="
echo ""
echo -e "${BLUE}📊 Your Carbon-Aware FinOps tool is now deployed:${NC}"
echo "  • AWS Account: $AWS_ACCOUNT_ID"
echo "  • Region: $AWS_REGION"  
echo "  • Project: $PROJECT_NAME"
echo "  • Lambda Function: $LAMBDA_FUNCTION_NAME"
echo "  • DynamoDB Table: $DYNAMODB_TABLE"
echo ""
echo -e "${BLUE}🔍 Tool will automatically analyze ALL EC2 instances in your account${NC}"
echo -e "${BLUE}⏰ Scheduler runs every hour to collect cost and carbon data${NC}"
echo ""
echo -e "${YELLOW}📈 Next steps:${NC}"
echo "1. Wait 1-2 hours for initial data collection"
echo "2. Run the dashboard: make dashboard"
echo "3. View results at: http://localhost:8050"
echo ""
echo -e "${BLUE}💡 Tip: Tag instances with 'ScheduleType=office-hours|weekdays-only|carbon-aware' for optimization${NC}"