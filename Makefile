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


# Infrastructure Management
infrastructure-plan: ## Plan Terraform deployment
	@echo "$(YELLOW)Planning infrastructure deployment...$(NC)"
	cd $(TERRAFORM_DIR) && $(TERRAFORM) init
	cd $(TERRAFORM_DIR) && ./build_lambda.sh
	cd $(TERRAFORM_DIR) && $(TERRAFORM) plan -var="aws_profile=$(AWS_PROFILE)" -var="aws_region=$(AWS_REGION)"
	@echo "$(GREEN)✅ Infrastructure plan complete$(NC)"

infrastructure-apply: ## Deploy infrastructure with Terraform  
	@echo "$(YELLOW)Deploying infrastructure...$(NC)"
	cd $(TERRAFORM_DIR) && $(TERRAFORM) init
	cd $(TERRAFORM_DIR) && ./build_lambda.sh
	cd $(TERRAFORM_DIR) && $(TERRAFORM) apply -var="aws_profile=$(AWS_PROFILE)" -var="aws_region=$(AWS_REGION)" -auto-approve
	@echo "$(GREEN)✅ Infrastructure deployed successfully$(NC)"

infrastructure-destroy: ## Destroy Terraform infrastructure
	@echo "$(RED)⚠️  WARNING: This will destroy all infrastructure!$(NC)"
	@read -p "Are you sure? Type 'yes' to continue: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		cd $(TERRAFORM_DIR) && $(TERRAFORM) destroy -var="aws_profile=$(AWS_PROFILE)" -var="aws_region=$(AWS_REGION)" -auto-approve; \
		echo "$(GREEN)✅ Infrastructure destroyed$(NC)"; \
	else \
		echo "$(BLUE)❌ Infrastructure destruction cancelled$(NC)"; \
	fi

infrastructure-status: ## Show infrastructure status
	@echo "$(YELLOW)Infrastructure Status:$(NC)"
	@cd $(TERRAFORM_DIR) && $(TERRAFORM) output -json 2>/dev/null | python -m json.tool || echo "No outputs yet. Run 'make infrastructure-apply' first."

# Secrets Management
secrets-setup: ## Interactive setup of API keys and secrets
	@echo "$(YELLOW)Setting up secrets...$(NC)"
	./$(VENV)/bin/python $(SCRIPTS_DIR)/setup_secrets.py --aws-profile $(AWS_PROFILE)
	@echo "$(GREEN)✅ Secrets setup complete$(NC)"


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

# System Status
status: ## Show system status
	@echo "$(YELLOW)System status check...$(NC)"
	@echo "$(BLUE)AWS connectivity:$(NC)"
	aws sts get-caller-identity --profile $(AWS_PROFILE) > /dev/null && echo "$(GREEN)✅ AWS connectivity OK$(NC)" || echo "$(RED)❌ AWS connectivity failed$(NC)"
	@echo "$(BLUE)Infrastructure status:$(NC)"
	cd $(TERRAFORM_DIR) && $(TERRAFORM) show -json 2>/dev/null | jq -r '.values.root_module.resources[]?.values.function_name // empty' | head -5 || echo "No infrastructure found"

# Lambda Management
enable-automation: ## Enable EventBridge schedules for automation
	@echo "$(YELLOW)Enabling automation schedules...$(NC)"
	aws events enable-rule --name carbon-aware-finops-scheduler-rule --region $(AWS_REGION) --profile $(AWS_PROFILE)
	aws events enable-rule --name carbon-aware-finops-rightsizing-rule --region $(AWS_REGION) --profile $(AWS_PROFILE)
	@echo "$(GREEN)✅ Automation enabled$(NC)"

disable-automation: ## Disable EventBridge schedules
	@echo "$(YELLOW)Disabling automation schedules...$(NC)"
	aws events disable-rule --name carbon-aware-finops-scheduler-rule --region $(AWS_REGION) --profile $(AWS_PROFILE) || true
	aws events disable-rule --name carbon-aware-finops-rightsizing-rule --region $(AWS_REGION) --profile $(AWS_PROFILE) || true
	@echo "$(GREEN)✅ Automation disabled$(NC)"

logs: ## View recent Lambda logs
	@echo "$(YELLOW)Recent Lambda logs:$(NC)"
	@echo "$(BLUE)Scheduler logs:$(NC)"
	aws logs tail /aws/lambda/carbon-aware-finops-scheduler --since 1h --region $(AWS_REGION) --profile $(AWS_PROFILE) 2>/dev/null || echo "No scheduler logs found"
	@echo "$(BLUE)Rightsizing logs:$(NC)"
	aws logs tail /aws/lambda/carbon-aware-finops-rightsizing --since 1h --region $(AWS_REGION) --profile $(AWS_PROFILE) 2>/dev/null || echo "No rightsizing logs found"

instances: ## List managed EC2 instances
	@echo "$(YELLOW)Managed EC2 instances:$(NC)"
	aws ec2 describe-instances \
		--filters "Name=tag:Project,Values=carbon-aware-finops" \
		--query 'Reservations[*].Instances[*].[InstanceId,State.Name,InstanceType,Tags[?Key==`Schedule`].Value|[0],Tags[?Key==`Name`].Value|[0]]' \
		--output table \
		--profile $(AWS_PROFILE)

	@echo "Approximate monthly costs ($(AWS_REGION)):"
	@echo "  - 4x t3.micro instances (on-demand): ~$$30"
	@echo "  - Lambda executions (96/day): ~$$0.50"
	@echo "  - DynamoDB: ~$$1"
	@echo "  - S3 storage: ~$$1"
	@echo "  - CloudWatch Logs: ~$$2"
	@echo "  $(GREEN)Total: ~$$35/month$(NC)"

# Development and Maintenance
clean: ## Clean temporary files and caches
	@echo "$(YELLOW)Cleaning temporary files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf .mypy_cache 2>/dev/null || true
	rm -rf carbon_aware_finops.egg-info 2>/dev/null || true
	find infrastructure/ -name "*.tfstate.backup" -delete 2>/dev/null || true
	find . -name "package-lock.json" -size -100c -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

clean-venv: ## Remove virtual environment
	@echo "$(YELLOW)Removing virtual environment...$(NC)"
	rm -rf $(VENV)
	@echo "$(GREEN)✅ Virtual environment removed$(NC)"

deep-clean: ## Deep clean including logs and terraform cache
	@echo "$(YELLOW)Performing deep cleanup...$(NC)"
	$(MAKE) clean
	rm -rf logs/*.log 2>/dev/null || true
	rm -rf infrastructure/terraform/.terraform 2>/dev/null || true
	rm -rf infrastructure/terraform/*.zip 2>/dev/null || true
	find . -name "*.DS_Store" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Deep cleanup complete$(NC)"

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
quick-start: ## Quick start: install dependencies and check status
	@echo "$(GREEN)🚀 Quick Start - Carbon-Aware FinOps$(NC)"
	$(MAKE) install
	$(MAKE) status
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

