# Makefile for Carbon-Aware FinOps Terraform Deployment
# Usage: make [target]

.PHONY: help init plan apply destroy clean build-lambda test-lambda

# Variables
TERRAFORM_DIR = .
PROJECT_ROOT = ../..
AWS_REGION = eu-central-1
AWS_PROFILE = default

# Colors
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "Carbon-Aware FinOps - Terraform Deployment"
	@echo "=========================================="
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "Quick start:"
	@echo "  1. make build-lambda  # Build Lambda packages"
	@echo "  2. make init         # Initialize Terraform"
	@echo "  3. make plan         # Review changes"
	@echo "  4. make apply        # Deploy infrastructure"

init: ## Initialize Terraform
	@echo "$(YELLOW)Initializing Terraform...$(NC)"
	terraform init
	@echo "$(GREEN)✅ Terraform initialized$(NC)"

build-lambda: ## Build Lambda deployment packages
	@echo "$(YELLOW)Building Lambda packages...$(NC)"
	@if [ -f build_lambda.sh ]; then \
		bash build_lambda.sh; \
	else \
		echo "$(RED)❌ build_lambda.sh not found. Creating it...$(NC)"; \
		make create-build-script; \
		bash build_lambda.sh; \
	fi

create-build-script: ## Create build_lambda.sh if it doesn't exist
	@echo "Creating build_lambda.sh..."
	@cat > build_lambda.sh < /dev/null || echo "Use the artifact content"
	@chmod +x build_lambda.sh
	@echo "$(GREEN)✅ build_lambda.sh created$(NC)"

plan: build-lambda ## Plan Terraform changes
	@echo "$(YELLOW)Planning Terraform changes...$(NC)"
	terraform plan -out=tfplan

plan-destroy: ## Plan destroy operation
	@echo "$(YELLOW)Planning destroy operation...$(NC)"
	terraform plan -destroy -out=tfplan-destroy

apply: ## Apply Terraform changes
	@echo "$(YELLOW)Applying Terraform changes...$(NC)"
	@if [ -f tfplan ]; then \
		terraform apply tfplan; \
		rm -f tfplan; \
	else \
		echo "$(RED)No plan file found. Run 'make plan' first.$(NC)"; \
		exit 1; \
	fi

apply-auto: build-lambda ## Apply without plan file (auto-approve)
	@echo "$(YELLOW)⚠️  Auto-applying Terraform changes...$(NC)"
	terraform apply -auto-approve

destroy: ## Destroy all infrastructure
	@echo "$(RED)⚠️  WARNING: This will destroy all infrastructure!$(NC)"
	@read -p "Are you sure? Type 'yes' to continue: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		terraform destroy -auto-approve; \
	else \
		echo "Destroy cancelled."; \
	fi

clean: ## Clean up temporary files
	@echo "$(YELLOW)Cleaning up...$(NC)"
	rm -rf .terraform/
	rm -f .terraform.lock.hcl
	rm -f terraform.tfstate*
	rm -f tfplan*
	rm -f lambda_layer.zip
	rm -f lambda_deployment.zip
	rm -rf build_tmp/
	@echo "$(GREEN)✅ Cleaned up$(NC)"

validate: ## Validate Terraform configuration
	@echo "$(YELLOW)Validating Terraform configuration...$(NC)"
	terraform validate
	@echo "$(GREEN)✅ Configuration is valid$(NC)"

fmt: ## Format Terraform files
	@echo "$(YELLOW)Formatting Terraform files...$(NC)"
	terraform fmt -recursive
	@echo "$(GREEN)✅ Formatted$(NC)"

test-lambda: ## Test Lambda function locally
	@echo "$(YELLOW)Testing Lambda function locally...$(NC)"
	@cd $(PROJECT_ROOT) && \
	python -c "from src.lambda.scheduler_handler import lambda_handler; \
	           result = lambda_handler({}, None); \
	           print('Lambda test result:', result)"

deploy-core: ## Deploy only core infrastructure (no Lambda)
	@echo "$(YELLOW)Deploying core infrastructure...$(NC)"
	terraform apply -target=aws_vpc.main \
	                -target=aws_subnet.public \
	                -target=aws_security_group.main \
	                -target=aws_dynamodb_table.state \
	                -target=aws_s3_bucket.data \
	                -auto-approve
	@echo "$(GREEN)✅ Core infrastructure deployed$(NC)"

deploy-instances: ## Deploy EC2 instances
	@echo "$(YELLOW)Deploying EC2 instances...$(NC)"
	terraform apply -target=module.test_instances \
	                -target='aws_instance.scheduled_instances["web-server"]' \
	                -target='aws_instance.scheduled_instances["app-server"]' \
	                -auto-approve
	@echo "$(GREEN)✅ EC2 instances deployed$(NC)"

deploy-lambda: build-lambda ## Deploy Lambda functions
	@echo "$(YELLOW)Deploying Lambda functions...$(NC)"
	terraform apply -target=aws_lambda_layer_version.python_dependencies \
	                -target=aws_lambda_function.scheduler \
	                -target=aws_lambda_function.rightsizing \
	                -auto-approve
	@echo "$(GREEN)✅ Lambda functions deployed$(NC)"

enable-schedules: ## Enable EventBridge schedules
	@echo "$(YELLOW)Enabling EventBridge schedules...$(NC)"
	aws events enable-rule --name carbon-aware-finops-scheduler-rule --region $(AWS_REGION) --profile $(AWS_PROFILE)
	aws events enable-rule --name carbon-aware-finops-rightsizing-rule --region $(AWS_REGION) --profile $(AWS_PROFILE)
	@echo "$(GREEN)✅ Schedules enabled$(NC)"

disable-schedules: ## Disable EventBridge schedules
	@echo "$(YELLOW)Disabling EventBridge schedules...$(NC)"
	aws events disable-rule --name carbon-aware-finops-scheduler-rule --region $(AWS_REGION) --profile $(AWS_PROFILE) || true
	aws events disable-rule --name carbon-aware-finops-rightsizing-rule --region $(AWS_REGION) --profile $(AWS_PROFILE) || true
	@echo "$(GREEN)✅ Schedules disabled$(NC)"

logs-scheduler: ## View scheduler Lambda logs
	@echo "$(YELLOW)Viewing scheduler Lambda logs...$(NC)"
	aws logs tail /aws/lambda/carbon-aware-finops-scheduler --follow --region $(AWS_REGION) --profile $(AWS_PROFILE)

logs-rightsizing: ## View rightsizing Lambda logs
	@echo "$(YELLOW)Viewing rightsizing Lambda logs...$(NC)"
	aws logs tail /aws/lambda/carbon-aware-finops-rightsizing --follow --region $(AWS_REGION) --profile $(AWS_PROFILE)

test-scheduler: ## Manually invoke scheduler Lambda
	@echo "$(YELLOW)Manually invoking scheduler Lambda...$(NC)"
	aws lambda invoke \
		--function-name carbon-aware-finops-scheduler \
		--region $(AWS_REGION) \
		--profile $(AWS_PROFILE) \
		--payload '{}' \
		response.json
	@cat response.json | python -m json.tool
	@rm -f response.json

cost-estimate: ## Estimate monthly costs
	@echo "$(YELLOW)Estimating monthly costs...$(NC)"
	@echo "Approximate monthly costs (eu-central-1):"
	@echo "  - 4x t3.micro instances (on-demand): ~$$30"
	@echo "  - Lambda executions (96/day): ~$$0.50"
	@echo "  - DynamoDB: ~$$1"
	@echo "  - S3 storage: ~$$1"
	@echo "  - CloudWatch Logs: ~$$2"
	@echo "  $(GREEN)Total: ~$$35/month$(NC)"
	@echo ""
	@echo "With optimization (50% shutdown time):"
	@echo "  $(GREEN)Estimated savings: ~$$15/month$(NC)"

status: ## Show infrastructure status
	@echo "$(YELLOW)Infrastructure Status:$(NC)"
	@echo ""
	@terraform output -json 2>/dev/null | python -m json.tool || echo "No outputs yet. Run 'make apply' first."
	@echo ""
	@echo "$(YELLOW)EC2 Instances:$(NC)"
	@aws ec2 describe-instances \
		--filters "Name=tag:Project,Values=carbon-aware-finops" \
		--query 'Reservations[*].Instances[*].{ID:InstanceId,Type:InstanceType,State:State.Name,Name:Tags[?Key==`Name`]|[0].Value}' \
		--output table \
		--region $(AWS_REGION) \
		--profile $(AWS_PROFILE) 2>/dev/null || echo "No instances found"

all: build-lambda init validate plan ## Run all preparation steps