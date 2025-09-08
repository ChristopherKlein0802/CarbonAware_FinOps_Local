# Carbon-Aware FinOps - Bachelor Thesis Dashboard
# Separate Dashboard and AWS Infrastructure Management

.PHONY: help setup-env dashboard deploy destroy test-apis test status instances keys cleanup _check-env deploy-aws destroy-aws
.DEFAULT_GOAL := help

# Configuration
PYTHON := python3
VENV := venv
# AWS configuration (will be overridden from .env if present)
AWS_PROFILE := carbon-finops-sandbox
AWS_REGION := eu-central-1

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
RED := \033[0;31m
BOLD := \033[1m
NC := \033[0m

help: ## 📋 Show available commands
	@echo "$(BOLD)$(GREEN)🎓 Carbon-Aware FinOps Dashboard - Bachelor Thesis$(NC)"
	@echo "======================================================="
	@echo "$(BLUE)Separate Dashboard & AWS Infrastructure Management$(NC)"
	@echo ""
	@echo "$(BOLD)🚀 Quick Start:$(NC)"
	@echo "  $(BLUE)make setup-env$(NC)  - Setup environment & API keys"
	@echo "  $(BLUE)make dashboard$(NC)  - 📊 Launch dashboard"
	@echo "  $(BLUE)make deploy$(NC)     - ☁️  Deploy AWS instances"
	@echo ""
	@echo "$(BOLD)📊 Dashboard & Testing:$(NC)"
	@echo "  $(BLUE)make dashboard$(NC)  - Launch analysis dashboard"
	@echo "  $(BLUE)make test-apis$(NC)  - Test API connections"
	@echo "  $(BLUE)make test$(NC)       - Run test suite"
	@echo "  $(BLUE)make keys$(NC)       - Check API key status"
	@echo ""
	@echo "$(BOLD)☁️  AWS Infrastructure:$(NC)"
	@echo "  $(BLUE)make deploy$(NC)     - Deploy 8 test instances"
	@echo "  $(BLUE)make destroy$(NC)    - Remove all AWS resources (⚠️  careful!)"
	@echo "  $(BLUE)make status$(NC)     - Show infrastructure status"
	@echo "  $(BLUE)make instances$(NC)  - List EC2 instances"
	@echo ""
	@echo "$(BOLD)🔧 Utilities:$(NC)"
	@echo "  $(BLUE)make cleanup$(NC)    - Clean temporary files"

# 🚀 ENVIRONMENT SETUP
setup-env: ## 🔧 Setup environment and API keys
	@echo "$(BOLD)$(GREEN)🔧 Carbon-Aware FinOps Environment Setup$(NC)"
	@echo "========================================="
	@echo "$(YELLOW)1/4 Creating Python virtual environment...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		$(PYTHON) -m venv $(VENV) && echo "$(GREEN)✅ Virtual environment created$(NC)" || echo "$(RED)❌ Error creating venv$(NC)"; \
	else \
		echo "$(GREEN)✅ Virtual environment already exists$(NC)"; \
	fi
	@./$(VENV)/bin/pip install --upgrade pip setuptools wheel > /dev/null 2>&1
	@echo "$(YELLOW)2/4 Installing Python dependencies...$(NC)"
	@./$(VENV)/bin/pip install -r requirements.txt > /dev/null 2>&1 && echo "$(GREEN)✅ Dependencies installed$(NC)" || echo "$(RED)❌ Dependency installation failed$(NC)"
	@echo "$(YELLOW)3/4 Setting up API keys...$(NC)"
	@if [ ! -f ".env" ]; then \
		echo "$(RED)❌ No .env file found$(NC)"; \
		echo "Create .env file with your API keys"; \
		exit 1; \
	else \
		echo "$(GREEN)✅ .env file found$(NC)"; \
	fi
	@echo "$(YELLOW)4/4 Testing API connections...$(NC)"
	@$(MAKE) test-apis
	@echo ""
	@echo "$(BOLD)$(GREEN)🎉 Environment Setup Complete!$(NC)"
	@echo "Next: Run $(BOLD)make dashboard$(NC) to start dashboard"

# 📊 DASHBOARD
dashboard: ## 📊 Launch Carbon-Aware FinOps Dashboard
	@echo "$(BOLD)$(GREEN)📊 Launching Carbon-Aware FinOps Dashboard$(NC)"
	@echo "==============================================="
	@echo "$(BLUE)Dashboard URL: http://127.0.0.1:8051$(NC)"
	@echo "$(BLUE)Press Ctrl+C to stop$(NC)"
	@echo ""
	@echo "$(YELLOW)Loading dashboard with:$(NC)"
	@echo "  ✅ ElectricityMap API (German grid data)"
	@echo "  ✅ Boavizta API (hardware power data)"
	@echo "  ✅ AWS Cost Explorer (if instances deployed)"
	@echo ""
	@if [ -f ".env" ]; then \
		set -a && source .env && set +a && ./$(VENV)/bin/python3 src/visualization/optimization_analysis_dashboard.py; \
	else \
		echo "$(YELLOW)⚠️  No .env file found, using demo mode$(NC)"; \
		./$(VENV)/bin/python3 src/visualization/optimization_analysis_dashboard.py; \
	fi

# ☁️  AWS INFRASTRUCTURE  
deploy: ## ☁️  Deploy 8 test instances to AWS
	@echo "$(BOLD)$(GREEN)☁️  Deploying AWS Infrastructure$(NC)"
	@echo "=================================="
	@echo "$(YELLOW)Deploying 8 test instances to AWS...$(NC)"
	@cd infrastructure/terraform && \
		terraform init && \
		terraform apply -auto-approve
	@echo ""
	@echo "$(BOLD)$(GREEN)🎉 AWS Deployment Complete!$(NC)"
	@echo "Instances will appear in dashboard within 60 seconds"
	@$(MAKE) status

deploy-aws: ## ☁️  Alias for deploy (backward compatibility)
	@$(MAKE) deploy

destroy: ## 🗑️  Destroy all AWS resources
	@echo "$(BOLD)$(RED)⚠️  Destroying AWS Infrastructure$(NC)"
	@echo "==================================="
	@echo "$(RED)This will remove all AWS resources!$(NC)"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	@cd infrastructure/terraform && terraform destroy -auto-approve
	@echo "$(GREEN)✅ AWS resources destroyed$(NC)"

destroy-aws: ## 🗑️  Alias for destroy (backward compatibility)
	@$(MAKE) destroy

# 🔍 MONITORING & STATUS
status: ## 📊 Show AWS infrastructure status
	@echo "$(BOLD)$(GREEN)📊 Infrastructure Status$(NC)"
	@echo "========================="
	@echo "$(YELLOW)AWS Profile:$(NC) $(AWS_PROFILE)"
	@echo "$(YELLOW)AWS Region:$(NC) $(AWS_REGION)"
	@echo ""
	@aws ec2 describe-instances --profile $(AWS_PROFILE) --region $(AWS_REGION) \
		--filters "Name=tag:Project,Values=carbon-aware-finops" "Name=instance-state-name,Values=running,stopped,pending" \
		--query 'Reservations[].Instances[].[InstanceId,InstanceType,State.Name,Tags[?Key==`Name`].Value|[0]]' \
		--output table || echo "$(RED)❌ No AWS access or instances found$(NC)"

instances: ## 💻 List managed EC2 instances
	@echo "$(BOLD)$(GREEN)💻 Managed EC2 Instances$(NC)"
	@echo "=========================="
	@aws ec2 describe-instances --profile $(AWS_PROFILE) --region $(AWS_REGION) \
		--filters "Name=tag:Project,Values=carbon-aware-finops" \
		--query 'Reservations[].Instances[].[InstanceId,InstanceType,State.Name,LaunchTime,Tags[?Key==`Name`].Value|[0],Tags[?Key==`ScheduleType`].Value|[0]]' \
		--output table || echo "$(RED)❌ No instances found$(NC)"

# 🧪 TESTING & APIs  
test-apis: ## 🧪 Test API connections
	@echo "$(BOLD)$(GREEN)🧪 Testing API Connections$(NC)"
	@echo "============================"
	@echo "$(YELLOW)1/3 Testing Boavizta API...$(NC)"
	@./$(VENV)/bin/python3 -c "from src.services.power_consumption_service import PowerConsumptionService; service = PowerConsumptionService(); result = service.get_instance_power_consumption('t3.medium'); print(f'✅ Boavizta API: {result.avg_power_watts}W avg power')" || echo "$(RED)❌ Boavizta API failed$(NC)"
	@echo "$(YELLOW)2/3 Testing ElectricityMap API...$(NC)"
	@if [ -f ".env" ]; then \
		set -a && source .env && set +a && ./$(VENV)/bin/python3 -c "from src.carbon.carbon_api_client import CarbonIntensityClient; client = CarbonIntensityClient(provider='electricitymap'); result = client.get_current_intensity('eu-central-1'); print(f'✅ ElectricityMap API: {result}g CO2/kWh')" 2>/dev/null || echo "$(YELLOW)⚠️  ElectricityMap API: Check API key in .env$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  No .env file - using demo mode$(NC)"; \
	fi
	@echo "$(YELLOW)3/3 Testing AWS access...$(NC)"
	@aws sts get-caller-identity --profile $(AWS_PROFILE) --query 'Account' --output text >/dev/null && echo "$(GREEN)✅ AWS access working$(NC)" || echo "$(RED)❌ AWS access failed$(NC)"

test: ## 🧪 Run test suite
	@echo "$(BOLD)$(GREEN)🧪 Running Test Suite$(NC)"
	@echo "===================="
	@echo "$(YELLOW)Running Python tests...$(NC)"
	@if [ -f "tests/test_carbon_api.py" ]; then \
		if [ -f ".env" ]; then set -a && source .env && set +a; fi && \
		./$(VENV)/bin/python3 -m pytest tests/ -v || echo "$(YELLOW)⚠️  Some tests failed$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  No test files found$(NC)"; \
	fi
	@echo ""
	@echo "$(YELLOW)Running integration tests...$(NC)"
	@if [ -f "tests/test_power_service.py" ]; then \
		if [ -f ".env" ]; then set -a && source .env && set +a; fi && \
		./$(VENV)/bin/python3 tests/test_power_service.py && echo "$(GREEN)✅ Power service test successful$(NC)" || echo "$(YELLOW)⚠️  Power service test had issues$(NC)"; \
	fi
	@echo ""
	@echo "$(YELLOW)Running demo scripts...$(NC)"
	@if [ -f "tests/demo_api_interaction.py" ]; then \
		if [ -f ".env" ]; then set -a && source .env && set +a; fi && \
		./$(VENV)/bin/python3 tests/demo_api_interaction.py && echo "$(GREEN)✅ API demo successful$(NC)" || echo "$(YELLOW)⚠️  API demo had issues$(NC)"; \
	fi

keys: ## 🔐 Check API key status
	@echo "$(BOLD)$(GREEN)🔐 API Key Status$(NC)"
	@echo "======================"
	@echo "$(YELLOW)Current API key status:$(NC)"
	@echo ""
	@echo "$(BLUE)1. ElectricityMap API:$(NC)"
	@if [ -f ".env" ] && grep -q "ELECTRICITYMAP_API_KEY=" .env; then \
		echo "   ✅ Configured in .env"; \
	else \
		echo "   ⚠️  Not configured - using demo fallback"; \
	fi
	@echo ""
	@echo "$(BLUE)2. AWS Credentials:$(NC)"
	@aws sts get-caller-identity --profile $(AWS_PROFILE) --query 'Account' --output text >/dev/null 2>&1 && echo "   ✅ AWS profile '$(AWS_PROFILE)' working" || echo "   ❌ AWS profile '$(AWS_PROFILE)' not configured"
	@echo ""
	@echo "$(BLUE)3. Boavizta API:$(NC)"
	@echo "   ✅ No API key required (public API)"
	@echo ""
	@echo "$(YELLOW)To update API keys:$(NC)"
	@echo "  • Edit .env file for ElectricityMap API key"
	@echo "  • Use 'aws configure sso' for AWS credentials"

# 🔧 UTILITIES
cleanup: ## 🧹 Clean temporary files and caches
	@echo "$(BOLD)$(GREEN)🧹 Cleaning up temporary files$(NC)"
	@echo "=================================="
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache/ 2>/dev/null || true
	@rm -rf build/ dist/ 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

# Development helpers (internal)
_check-env:
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(RED)❌ Virtual environment not found. Run 'make setup-env' first$(NC)"; \
		exit 1; \
	fi