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

infrastructure-plan: ## Plan Terraform deployment
	@echo "$(YELLOW)Planning infrastructure deployment...$(NC)"
	cd $(TERRAFORM_DIR) && $(TERRAFORM) plan -var="aws_profile=$(AWS_PROFILE)" -var="aws_region=$(AWS_REGION)"
	@echo "$(GREEN)✅ Infrastructure plan complete$(NC)"

infrastructure-apply: ## Deploy infrastructure with Terraform
	@echo "$(YELLOW)Deploying infrastructure...$(NC)"
	cd $(TERRAFORM_DIR) && $(TERRAFORM) apply -var="aws_profile=$(AWS_PROFILE)" -var="aws_region=$(AWS_REGION)" -auto-approve
	@echo "$(GREEN)✅ Infrastructure deployed successfully$(NC)"

infrastructure-destroy: ## Destroy Terraform infrastructure
	@echo "$(RED)⚠️  WARNING: This will destroy all infrastructure!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		cd $(TERRAFORM_DIR) && $(TERRAFORM) destroy -var="aws_profile=$(AWS_PROFILE)" -var="aws_region=$(AWS_REGION)" -auto-approve; \
		echo "$(GREEN)✅ Infrastructure destroyed$(NC)"; \
	else \
		echo "$(BLUE)❌ Infrastructure destruction cancelled$(NC)"; \
	fi

infrastructure-output: ## Show Terraform outputs
	@echo "$(YELLOW)Infrastructure outputs:$(NC)"
	cd $(TERRAFORM_DIR) && $(TERRAFORM) output

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
logs: ## View application logs
	@echo "$(YELLOW)Application logs:$(NC)"
	@find logs -name "*.log" -type f -exec echo "$(BLUE)=== {} ===$(NC)" \; -exec tail -20 {} \; 2>/dev/null || echo "$(YELLOW)⚠️  No log files found in logs/ directory$(NC)"

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