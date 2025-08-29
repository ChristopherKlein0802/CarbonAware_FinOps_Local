#!/bin/bash
set -e

echo "🚀 Carbon-Aware FinOps Deployment Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is not installed${NC}"
        exit 1
    fi
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI is not installed${NC}"
        exit 1
    fi
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        echo -e "${RED}❌ Terraform is not installed${NC}"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}❌ AWS credentials not configured${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All prerequisites met${NC}"
}

# Setup Python environment
setup_python() {
    echo -e "${YELLOW}Setting up Python environment...${NC}"
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -e .
    
    echo -e "${GREEN}✅ Python environment ready${NC}"
}

# Deploy infrastructure
deploy_infrastructure() {
    echo -e "${YELLOW}Deploying infrastructure...${NC}"
    
    cd infrastructure/terraform
    
    # Initialize Terraform
    terraform init
    
    # Create tfvars file
    cat > terraform.tfvars <<EOF
aws_region     = "eu-central-1"
aws_account_id = "273146546541"
aws_profile    = "default"
project_name   = "carbon-aware-finops"
environment    = "development"
EOF
    
    # Plan deployment
    terraform plan -out=tfplan
    
    # Apply with auto-approve for CI/CD
    terraform apply tfplan
    
    # Save outputs
    terraform output -json > ../../outputs.json
    
    cd ../..
    echo -e "${GREEN}✅ Infrastructure deployed${NC}"
}

# Package and deploy Lambda functions
deploy_lambdas() {
    echo -e "${YELLOW}Deploying Lambda functions...${NC}"
    
    # Create Lambda layer
    mkdir -p lambda_layer/python
    pip install -r requirements.txt -t lambda_layer/python/
    cd lambda_layer
    zip -r ../lambda_layer.zip . -q
    cd ..
    rm -rf lambda_layer
    
    # Create Lambda deployment package
    zip -r lambda_deployment.zip src/ -x "*.pyc" -x "*__pycache__*" -q
    
    # Move packages to Terraform directory
    mv lambda_layer.zip infrastructure/terraform/
    mv lambda_deployment.zip infrastructure/terraform/
    
    # Apply Lambda-specific resources
    cd infrastructure/terraform
    terraform apply -target=aws_lambda_function.scheduler -auto-approve
    terraform apply -target=aws_lambda_function.rightsizing -auto-approve
    cd ../..
    
    echo -e "${GREEN}✅ Lambda functions deployed${NC}"
}

# Initialize database
initialize_database() {
    echo -e "${YELLOW}Initializing database...${NC}"
    
    # Run baseline collection
    python scripts/collect_baseline.py --days 1 --region eu-central-1
    
    echo -e "${GREEN}✅ Database initialized${NC}"
}

# Start dashboard
start_dashboard() {
    echo -e "${YELLOW}Starting dashboard...${NC}"
    
    # Create dashboard service
    cat > dashboard.service <<EOF
[Unit]
Description=Carbon-Aware FinOps Dashboard
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/python src/reporting/realtime_dashboard.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF
    
    # Start dashboard in background
    nohup python src/reporting/realtime_dashboard.py > dashboard.log 2>&1 &
    
    echo -e "${GREEN}✅ Dashboard started on http://localhost:8050${NC}"
}

# Main deployment
main() {
    echo "Starting deployment at $(date)"
    
    check_prerequisites
    setup_python
    deploy_infrastructure
    deploy_lambdas
    initialize_database
    start_dashboard
    
    echo -e "${GREEN}🎉 Deployment complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Check the dashboard at http://localhost:8050"
    echo "2. Monitor Lambda executions in CloudWatch"
    echo "3. Review cost savings in Cost Explorer"
    echo ""
    echo "Useful commands:"
    echo "  terraform destroy  # Tear down infrastructure"
    echo "  tail -f dashboard.log  # View dashboard logs"
    echo "  aws logs tail /aws/lambda/carbon-aware-finops-scheduler  # View Lambda logs"
}

# Run main function
main