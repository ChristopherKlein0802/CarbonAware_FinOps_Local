# Carbon-Aware FinOps Makefile
# Provides convenient commands for development, testing, and deployment

.PHONY: help install test lint format clean build deploy infrastructure dashboard scheduler rightsizing baseline secrets validate docs

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip3
VENV := venv
TERRAFORM := terraform
AWS_PROFILE := carbon-finops-sandbox
AWS_REGION := eu-central-1
TERRAFORM_DIR := infrastructure/terraform
SCRIPTS_DIR := scripts
SRC_DIR := src

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)Carbon-Aware FinOps - Available Commands$(NC)"
	@echo "=========================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(BLUE)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Environment Setup
install: ## Install Python dependencies and setup virtual environment
	@echo "$(YELLOW)Setting up virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	./$(VENV)/bin/pip install --upgrade pip
	./$(VENV)/bin/pip install -r requirements.txt
	@echo "$(GREEN)✅ Virtual environment setup complete$(NC)"
	@echo "$(BLUE)To activate: source $(VENV)/bin/activate$(NC)"

install-dev: install ## Install development dependencies
	@echo "$(YELLOW)Installing development dependencies...$(NC)"
	./$(VENV)/bin/pip install -r requirements-dev.txt || echo "$(YELLOW)⚠️  requirements-dev.txt not found, skipping$(NC)"
	@echo "$(GREEN)✅ Development dependencies installed$(NC)"

# Code Quality
lint: ## Run code linting with flake8
	@echo "$(YELLOW)Running code linting...$(NC)"
	./$(VENV)/bin/flake8 $(SRC_DIR) --max-line-length=120 --extend-ignore=E203,W503 || echo "$(RED)❌ Linting issues found$(NC)"
	@echo "$(GREEN)✅ Linting complete$(NC)"

format: ## Format code with black
	@echo "$(YELLOW)Formatting code...$(NC)"
	./$(VENV)/bin/black $(SRC_DIR) --line-length=120
	@echo "$(GREEN)✅ Code formatting complete$(NC)"

type-check: ## Run type checking with mypy
	@echo "$(YELLOW)Running type checks...$(NC)"
	./$(VENV)/bin/mypy $(SRC_DIR) --ignore-missing-imports || echo "$(RED)❌ Type checking issues found$(NC)"
	@echo "$(GREEN)✅ Type checking complete$(NC)"

# Testing
test: ## Run all tests
	@echo "$(YELLOW)Running tests...$(NC)"
	./$(VENV)/bin/pytest tests/ -v --tb=short
	@echo "$(GREEN)✅ Tests complete$(NC)"

test-coverage: ## Run tests with coverage report
	@echo "$(YELLOW)Running tests with coverage...$(NC)"
	./$(VENV)/bin/pytest tests/ -v --cov=$(SRC_DIR) --cov-report=html --cov-report=term
	@echo "$(GREEN)✅ Coverage report generated$(NC)"
	@echo "$(BLUE)📊 View HTML report: open htmlcov/index.html$(NC)"

test-carbon: ## Run carbon intensity API tests
	@echo "$(YELLOW)Testing carbon API integration...$(NC)"
	./$(VENV)/bin/pytest tests/test_carbon.py -v
	@echo "$(GREEN)✅ Carbon API tests complete$(NC)"

test-cost: ## Run cost analysis tests
	@echo "$(YELLOW)Testing cost analysis...$(NC)"
	./$(VENV)/bin/pytest tests/test_cost.py -v
	@echo "$(GREEN)✅ Cost analysis tests complete$(NC)"

# Infrastructure Management
infrastructure-init: ## Initialize Terraform
	@echo "$(YELLOW)Initializing Terraform...$(NC)"
	cd $(TERRAFORM_DIR) && $(TERRAFORM) init
	@echo "$(GREEN)✅ Terraform initialized$(NC)"

infrastructure-validate: ## Validate Terraform configuration
	@echo "$(YELLOW)Validating Terraform configuration...$(NC)"
	cd $(TERRAFORM_DIR) && $(TERRAFORM) validate
	@echo "$(GREEN)✅ Configuration is valid$(NC)"

infrastructure-format: ## Format Terraform files
	@echo "$(YELLOW)Formatting Terraform files...$(NC)"
	cd $(TERRAFORM_DIR) && $(TERRAFORM) fmt -recursive
	@echo "$(GREEN)✅ Formatted$(NC)"

infrastructure-build: ## Build Lambda deployment packages
	@echo "$(YELLOW)Building Lambda packages...$(NC)"
	cd $(TERRAFORM_DIR) && $(MAKE) build-lambda
	@echo "$(GREEN)✅ Lambda packages built$(NC)"

infrastructure-plan: ## Plan Terraform deployment
	@echo "$(YELLOW)Planning infrastructure deployment...$(NC)"
	cd $(TERRAFORM_DIR) && $(TERRAFORM) plan -var="aws_profile=$(AWS_PROFILE)" -var="aws_region=$(AWS_REGION)" -out=tfplan
	@echo "$(GREEN)✅ Infrastructure plan complete$(NC)"

infrastructure-apply: infrastructure-build ## Deploy infrastructure with Terraform
	@echo "$(YELLOW)Deploying infrastructure...$(NC)"
	cd $(TERRAFORM_DIR) && $(TERRAFORM) apply -var="aws_profile=$(AWS_PROFILE)" -var="aws_region=$(AWS_REGION)" -auto-approve
	@echo "$(GREEN)✅ Infrastructure deployed successfully$(NC)"

infrastructure-apply-plan: ## Apply using saved plan file
	@echo "$(YELLOW)Applying Terraform plan...$(NC)"
	cd $(TERRAFORM_DIR) && \
	if [ -f tfplan ]; then \
		$(TERRAFORM) apply tfplan && rm -f tfplan; \
	else \
		echo "$(RED)No plan file found. Run 'make infrastructure-plan' first.$(NC)"; \
		exit 1; \
	fi

infrastructure-destroy: ## Destroy Terraform infrastructure
	@echo "$(RED)⚠️  WARNING: This will destroy all infrastructure!$(NC)"
	@read -p "Are you sure? Type 'yes' to continue: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		cd $(TERRAFORM_DIR) && $(TERRAFORM) destroy -var="aws_profile=$(AWS_PROFILE)" -var="aws_region=$(AWS_REGION)" -auto-approve; \
		echo "$(GREEN)✅ Infrastructure destroyed$(NC)"; \
	else \
		echo "$(BLUE)❌ Infrastructure destruction cancelled$(NC)"; \
	fi

infrastructure-output: ## Show Terraform outputs
	@echo "$(YELLOW)Infrastructure outputs:$(NC)"
	cd $(TERRAFORM_DIR) && $(TERRAFORM) output

infrastructure-clean: ## Clean up Terraform temporary files
	@echo "$(YELLOW)Cleaning up Terraform files...$(NC)"
	cd $(TERRAFORM_DIR) && rm -rf .terraform/ .terraform.lock.hcl terraform.tfstate* tfplan* lambda_*.zip build_tmp/
	@echo "$(GREEN)✅ Terraform cleanup complete$(NC)"

# Partial Infrastructure Deployment
deploy-core: ## Deploy only core infrastructure (VPC, DynamoDB, S3)
	@echo "$(YELLOW)Deploying core infrastructure...$(NC)"
	cd $(TERRAFORM_DIR) && $(TERRAFORM) apply \
		-target=aws_vpc.main \
		-target=aws_subnet.public \
		-target=aws_security_group.main \
		-target=aws_dynamodb_table.state \
		-target=aws_dynamodb_table.rightsizing \
		-target=aws_dynamodb_table.costs \
		-target=aws_s3_bucket.data \
		-var="aws_profile=$(AWS_PROFILE)" -var="aws_region=$(AWS_REGION)" \
		-auto-approve
	@echo "$(GREEN)✅ Core infrastructure deployed$(NC)"

deploy-instances: ## Deploy EC2 instances
	@echo "$(YELLOW)Deploying EC2 instances...$(NC)"
	cd $(TERRAFORM_DIR) && $(TERRAFORM) apply \
		-target=module.test_instances \
		-target='aws_instance.scheduled_instances["web-server"]' \
		-target='aws_instance.scheduled_instances["app-server"]' \
		-target='aws_instance.scheduled_instances["db-server"]' \
		-target='aws_instance.scheduled_instances["batch-server"]' \
		-var="aws_profile=$(AWS_PROFILE)" -var="aws_region=$(AWS_REGION)" \
		-auto-approve
	@echo "$(GREEN)✅ EC2 instances deployed$(NC)"

deploy-lambda: infrastructure-build ## Deploy Lambda functions
	@echo "$(YELLOW)Deploying Lambda functions...$(NC)"
	cd $(TERRAFORM_DIR) && $(TERRAFORM) apply \
		-target=aws_lambda_layer_version.python_dependencies \
		-target=aws_lambda_function.scheduler \
		-target=aws_lambda_function.rightsizing \
		-var="aws_profile=$(AWS_PROFILE)" -var="aws_region=$(AWS_REGION)" \
		-auto-approve
	@echo "$(GREEN)✅ Lambda functions deployed$(NC)"

# Secrets Management
secrets-setup: ## Interactive setup of API keys and secrets
	@echo "$(YELLOW)Setting up secrets...$(NC)"
	./$(VENV)/bin/python $(SCRIPTS_DIR)/setup_secrets.py --aws-profile $(AWS_PROFILE)
	@echo "$(GREEN)✅ Secrets setup complete$(NC)"

secrets-setup-env: ## Setup secrets using environment variables
	@echo "$(YELLOW)Setting up secrets from environment...$(NC)"
	./$(VENV)/bin/python $(SCRIPTS_DIR)/setup_secrets.py --from-env --aws-profile $(AWS_PROFILE)
	@echo "$(GREEN)✅ Secrets setup from environment complete$(NC)"

secrets-validate: ## Validate secrets configuration
	@echo "$(YELLOW)Validating secrets...$(NC)"
	./$(VENV)/bin/python $(SCRIPTS_DIR)/setup_secrets.py --validate-only --aws-profile $(AWS_PROFILE)
	@echo "$(GREEN)✅ Secrets validation complete$(NC)"

# Data Collection and Analysis
baseline: ## Collect baseline data from AWS
	@echo "$(YELLOW)Collecting baseline data...$(NC)"
	./$(VENV)/bin/python $(SCRIPTS_DIR)/collect_baseline.py --profile $(AWS_PROFILE)
	@echo "$(GREEN)✅ Baseline data collection complete$(NC)"

# Application Components
scheduler: ## Run carbon-aware scheduler
	@echo "$(YELLOW)Starting carbon-aware scheduler...$(NC)"
	./$(VENV)/bin/python $(SRC_DIR)/automation/shutdown_scheduler.py
	@echo "$(GREEN)✅ Scheduler execution complete$(NC)"

rightsizing: ## Run rightsizing analysis
	@echo "$(YELLOW)Running rightsizing analysis...$(NC)"
	./$(VENV)/bin/python $(SRC_DIR)/lambda/rightsizing_handler.py
	@echo "$(GREEN)✅ Rightsizing analysis complete$(NC)"

dashboard: ## Launch real-time dashboard
	@echo "$(YELLOW)Starting dashboard server...$(NC)"
	@echo "$(BLUE)🌐 Dashboard will be available at: http://localhost:8050$(NC)"
	./$(VENV)/bin/python $(SRC_DIR)/reporting/realtime_dashboard.py

# Deployment and Operations
deploy-full: infrastructure-apply secrets-setup baseline ## Full deployment: infrastructure + secrets + baseline
	@echo "$(GREEN)🎉 Full deployment complete!$(NC)"
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "  • Run scheduler: make scheduler"
	@echo "  • Run rightsizing: make rightsizing"  
	@echo "  • Launch dashboard: make dashboard"

run-system: ## Run the complete carbon-aware system
	@echo "$(YELLOW)Running complete carbon-aware system...$(NC)"
	@echo "$(BLUE)📊 Running baseline collection...$(NC)"
	$(MAKE) baseline
	@echo "$(BLUE)⚡ Running scheduler...$(NC)"
	$(MAKE) scheduler
	@echo "$(BLUE)📈 Running rightsizing analysis...$(NC)"
	$(MAKE) rightsizing
	@echo "$(GREEN)✅ System execution complete$(NC)"
	@echo "$(BLUE)💡 Launch dashboard: make dashboard$(NC)"

# Validation and Verification
validate: ## Validate entire system setup
	@echo "$(YELLOW)Validating system setup...$(NC)"
	$(MAKE) secrets-validate
	$(MAKE) test
	@echo "$(BLUE)Testing AWS connectivity...$(NC)"
	aws sts get-caller-identity --profile $(AWS_PROFILE) > /dev/null && echo "$(GREEN)✅ AWS connectivity OK$(NC)" || echo "$(RED)❌ AWS connectivity failed$(NC)"
	@echo "$(GREEN)✅ System validation complete$(NC)"

check-aws: ## Check AWS configuration and connectivity
	@echo "$(YELLOW)Checking AWS configuration...$(NC)"
	@echo "$(BLUE)Current AWS identity:$(NC)"
	aws sts get-caller-identity --profile $(AWS_PROFILE)
	@echo "$(BLUE)Available regions:$(NC)"
	aws ec2 describe-regions --profile $(AWS_PROFILE) --query 'Regions[*].RegionName' --output table
	@echo "$(GREEN)✅ AWS check complete$(NC)"

# Monitoring and Observability
# Lambda Management
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

test-lambda-scheduler: ## Manually invoke scheduler Lambda
	@echo "$(YELLOW)Manually invoking scheduler Lambda...$(NC)"
	aws lambda invoke \
		--function-name carbon-aware-finops-scheduler \
		--region $(AWS_REGION) \
		--profile $(AWS_PROFILE) \
		--payload '{}' \
		response.json
	@cat response.json | python -m json.tool
	@rm -f response.json

test-lambda-rightsizing: ## Manually invoke rightsizing Lambda
	@echo "$(YELLOW)Manually invoking rightsizing Lambda...$(NC)"
	aws lambda invoke \
		--function-name carbon-aware-finops-rightsizing \
		--region $(AWS_REGION) \
		--profile $(AWS_PROFILE) \
		--payload '{}' \
		response.json
	@cat response.json | python -m json.tool
	@rm -f response.json

logs: ## View application logs
	@echo "$(YELLOW)Application logs:$(NC)"
	@find logs -name "*.log" -type f -exec echo "$(BLUE)=== {} ===$(NC)" \; -exec tail -20 {} \; 2>/dev/null || echo "$(YELLOW)⚠️  No log files found in logs/ directory$(NC)"

logs-scheduler: ## View scheduler Lambda logs
	@echo "$(YELLOW)Viewing scheduler Lambda logs...$(NC)"
	aws logs tail /aws/lambda/carbon-aware-finops-scheduler --follow --region $(AWS_REGION) --profile $(AWS_PROFILE)

logs-rightsizing: ## View rightsizing Lambda logs
	@echo "$(YELLOW)Viewing rightsizing Lambda logs...$(NC)"
	aws logs tail /aws/lambda/carbon-aware-finops-rightsizing --follow --region $(AWS_REGION) --profile $(AWS_PROFILE)

metrics: ## Show CloudWatch metrics
	@echo "$(YELLOW)Fetching CloudWatch metrics...$(NC)"
	aws cloudwatch get-metric-statistics \
		--namespace CarbonAwareFinOps \
		--metric-name InstanceShutdown \
		--start-time $$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
		--end-time $$(date -u +%Y-%m-%dT%H:%M:%SZ) \
		--period 3600 \
		--statistics Sum \
		--profile $(AWS_PROFILE) \
		--output table

instances: ## List managed EC2 instances
	@echo "$(YELLOW)Managed EC2 instances:$(NC)"
	aws ec2 describe-instances \
		--filters "Name=tag:Project,Values=carbon-aware-finops" \
		--query 'Reservations[*].Instances[*].[InstanceId,State.Name,InstanceType,Tags[?Key==`Schedule`].Value|[0],Tags[?Key==`Name`].Value|[0]]' \
		--output table \
		--profile $(AWS_PROFILE)

cost-estimate: ## Estimate monthly costs
	@echo "$(YELLOW)Estimating monthly costs...$(NC)"
	@echo "Approximate monthly costs ($(AWS_REGION)):"
	@echo "  - 4x t3.micro instances (on-demand): ~$$30"
	@echo "  - Lambda executions (96/day): ~$$0.50"
	@echo "  - DynamoDB: ~$$1"
	@echo "  - S3 storage: ~$$1"
	@echo "  - CloudWatch Logs: ~$$2"
	@echo "  $(GREEN)Total: ~$$35/month$(NC)"
	@echo ""
	@echo "With optimization (50% shutdown time):"
	@echo "  $(GREEN)Estimated savings: ~$$15/month$(NC)"

# Development and Maintenance
clean: ## Clean temporary files and caches
	@echo "$(YELLOW)Cleaning temporary files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

clean-venv: ## Remove virtual environment
	@echo "$(YELLOW)Removing virtual environment...$(NC)"
	rm -rf $(VENV)
	@echo "$(GREEN)✅ Virtual environment removed$(NC)"

reset: clean clean-venv ## Full reset: clean files and remove venv
	@echo "$(GREEN)✅ Full reset complete$(NC)"

# Documentation
docs: ## Generate documentation
	@echo "$(YELLOW)Generating documentation...$(NC)"
	@echo "$(BLUE)📚 Main documentation: README.md$(NC)"
	@echo "$(BLUE)🏗️  Architecture: docs/architecture.md (if exists)$(NC)"
	@echo "$(BLUE)🔧 Setup guide: Complete setup instructions in README$(NC)"
	@echo "$(GREEN)✅ Documentation ready$(NC)"

# Quick Start Workflows
quick-start: ## Quick start: install dependencies and validate setup
	@echo "$(GREEN)🚀 Quick Start - Carbon-Aware FinOps$(NC)"
	$(MAKE) install
	$(MAKE) validate
	@echo "$(GREEN)✅ Quick start complete!$(NC)"
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "  • Setup infrastructure: make infrastructure-apply"
	@echo "  • Configure secrets: make secrets-setup"
	@echo "  • Collect baseline: make baseline"
	@echo "  • Run system: make run-system"

dev-setup: ## Development setup: install dev dependencies and run quality checks
	@echo "$(GREEN)🛠️  Development Setup$(NC)"
	$(MAKE) install-dev
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) test
	@echo "$(GREEN)✅ Development environment ready!$(NC)"

optimize: ## Run project optimization analysis
	@echo "$(YELLOW)Running project optimization analysis...$(NC)"
	./$(VENV)/bin/python $(SCRIPTS_DIR)/optimize_project.py
	@echo "$(GREEN)✅ Optimization analysis complete$(NC)"
	@echo "$(BLUE)📄 Check OPTIMIZATION_REPORT.md for details$(NC)"

# Status and Information
status: ## Show system status
	@echo "$(GREEN)📊 Carbon-Aware FinOps System Status$(NC)"
	@echo "===================================="
	@echo "$(BLUE)Environment:$(NC)"
	@echo "  Python: $$($(PYTHON) --version 2>&1)"
	@echo "  Virtual Env: $$([ -d $(VENV) ] && echo '✅ Present' || echo '❌ Missing')"
	@echo "  AWS Profile: $(AWS_PROFILE)"
	@echo "  AWS Region: $(AWS_REGION)"
	@echo ""
	@echo "$(BLUE)Infrastructure:$(NC)"
	@cd $(TERRAFORM_DIR) && $(TERRAFORM) workspace show 2>/dev/null | sed 's/^/  Workspace: /' || echo "  Workspace: Not initialized"
	@echo ""
	@echo "$(BLUE)Quick Actions:$(NC)"
	@echo "  • Full deployment: make deploy-full"
	@echo "  • Run system: make run-system"
	@echo "  • Launch dashboard: make dashboard"

version: ## Show version information
	@echo "$(GREEN)Carbon-Aware FinOps Framework$(NC)"
	@echo "Version: 1.0.0"
	@echo "Python: $$($(PYTHON) --version 2>&1)"
	@echo "Terraform: $$($(TERRAFORM) version -json 2>/dev/null | jq -r '.terraform_version' 2>/dev/null || echo 'Not available')"
	@echo "AWS CLI: $$(aws --version 2>&1 | head -n1)"

# Emergency Commands
emergency-stop: ## Emergency stop: terminate all running instances
	@echo "$(RED)🚨 EMERGENCY STOP - Terminating managed instances$(NC)"
	@read -p "This will STOP all managed instances. Continue? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		aws ec2 describe-instances \
			--filters "Name=tag:Project,Values=carbon-aware-finops" "Name=instance-state-name,Values=running" \
			--query 'Reservations[*].Instances[*].InstanceId' \
			--output text \
			--profile $(AWS_PROFILE) | \
		xargs -r aws ec2 stop-instances --instance-ids --profile $(AWS_PROFILE) && \
		echo "$(GREEN)✅ Emergency stop complete$(NC)"; \
	else \
		echo "$(BLUE)❌ Emergency stop cancelled$(NC)"; \
	fi

# Health Checks
health-check: ## Comprehensive system health check
	@echo "$(YELLOW)Running comprehensive health check...$(NC)"
	@echo "$(BLUE)1. Checking Python environment...$(NC)"
	@$(MAKE) --quiet validate || echo "$(RED)❌ Validation failed$(NC)"
	@echo "$(BLUE)2. Checking AWS connectivity...$(NC)"
	@$(MAKE) --quiet check-aws || echo "$(RED)❌ AWS connectivity failed$(NC)"
	@echo "$(BLUE)3. Checking infrastructure...$(NC)"
	@cd $(TERRAFORM_DIR) && $(TERRAFORM) plan -detailed-exitcode -var="aws_profile=$(AWS_PROFILE)" -var="aws_region=$(AWS_REGION)" > /dev/null 2>&1 && echo "$(GREEN)✅ Infrastructure in sync$(NC)" || echo "$(YELLOW)⚠️  Infrastructure changes needed$(NC)"
	@echo "$(GREEN)✅ Health check complete$(NC)"