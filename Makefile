# Carbon-Aware FinOps - Bachelor Thesis
# Essential Development Workflow
# ===============================

.PHONY: help setup test test-unit test-integration dashboard validate-aws plan deploy status refresh destroy clean
.DEFAULT_GOAL := help

# Configuration
PYTHON := python3
VENV := venv
VENV_BIN := $(VENV)/bin
PIP := $(VENV_BIN)/pip
PYTHON_VENV := $(VENV_BIN)/python
STREAMLIT_PORT := 8501
AWS_PROFILE := carbon-finops-sandbox

# Simplified AWS Account Detection
define get_aws_account
	echo "$(BLUE)🔍 Detecting AWS Account...$(NC)" && \
	scripts/ensure_aws_session.sh $(AWS_PROFILE) >/dev/null && \
	AWS_ACCOUNT_ID=$$(aws sts get-caller-identity --profile $(AWS_PROFILE) --query Account --output text 2>/dev/null) && \
	if [ -z "$$AWS_ACCOUNT_ID" ]; then \
		echo "$(RED)❌ Unable to detect AWS account. Check SSO configuration for profile $(AWS_PROFILE).$(NC)"; \
		exit 1; \
	fi && \
	echo "$(GREEN)✅ Account: $$AWS_ACCOUNT_ID$(NC)"
endef

# Colors
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
RED := \033[0;31m
BOLD := \033[1m
NC := \033[0m

# Check if virtual environment exists
VENV_EXISTS := $(shell test -d $(VENV) && echo "yes" || echo "no")

# Shared function for venv validation
define check_venv
	@if [ "$(VENV_EXISTS)" = "no" ]; then \
		echo "$(RED)❌ Virtual environment not found. Run 'make setup' first$(NC)"; \
		exit 1; \
	fi
endef

help: ## 📋 Show available commands
	@echo "$(BOLD)$(GREEN)🎓 Carbon-Aware FinOps Dashboard$(NC)"
	@echo "================================="
	@echo ""
	@echo "$(BOLD)🚀 Essential Commands:$(NC)"
	@echo "  $(BLUE)make setup$(NC)     - Setup environment & install dependencies"
	@echo "  $(BLUE)make validate$(NC)  - Validate system configuration"
	@echo "  $(BLUE)make dashboard$(NC) - Launch Streamlit dashboard"
	@echo "  $(BLUE)make test$(NC)      - Run all tests"
	@echo "  $(BLUE)make test-unit$(NC) - Run only unit tests"
	@echo "  $(BLUE)make lint$(NC)      - Basic code quality check"
	@echo ""
	@echo "$(BOLD)☁️  AWS Infrastructure:$(NC)"
	@echo "  $(BLUE)make validate-aws$(NC) - Validate AWS SSO session"
	@echo "  $(BLUE)make plan$(NC)      - Show deployment plan"
	@echo "  $(BLUE)make deploy$(NC)    - Deploy test infrastructure"
	@echo "  $(BLUE)make status$(NC)    - Show infrastructure status"
	@echo "  $(BLUE)make refresh$(NC)   - Refresh infrastructure state"
	@echo "  $(BLUE)make destroy$(NC)   - Remove AWS resources"
	@echo ""
	@echo "$(BOLD)🛠️  Utilities:$(NC)"
	@echo "  $(BLUE)make clean$(NC)     - Clean temporary files"
	@echo "  $(BLUE)make help$(NC)      - Show this help"

setup: ## Complete environment setup
	@echo "$(YELLOW)📦 Setting up development environment...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(YELLOW)Creating virtual environment...$(NC)"; \
		$(PYTHON) -m venv $(VENV); \
	fi
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Setup complete!$(NC)"
	@echo "$(BLUE)💡 Next: Copy .env.example to .env and run 'make dashboard'$(NC)"

validate: ## Validate system configuration
	@echo "$(YELLOW)🔍 Validating system configuration...$(NC)"
	$(call check_venv)
	@echo "$(GREEN)✅ System configuration validated$(NC)"

dashboard: ## Launch Streamlit dashboard
	@echo "$(YELLOW)🚀 Starting dashboard...$(NC)"
	$(call check_venv)
	@echo "$(BLUE)📊 Opening at: http://localhost:$(STREAMLIT_PORT)$(NC)"
	PYTHONPATH=. $(VENV_BIN)/streamlit run src/app.py --server.port=$(STREAMLIT_PORT)

test: ## Run all tests
	@echo "$(YELLOW)🧪 Running tests...$(NC)"
	$(call check_venv)
	$(PYTHON_VENV) -m pytest tests/ -v
	@echo "$(GREEN)✅ Tests completed$(NC)"

test-unit: ## Run only unit tests
	@echo "$(YELLOW)🧪 Running unit tests...$(NC)"
	$(call check_venv)
	$(PYTHON_VENV) -m pytest tests/unit/ -v
	@echo "$(GREEN)✅ Unit tests completed$(NC)"

test-integration: ## Run integration tests (requires live credentials)
	@echo "$(YELLOW)🧪 Running integration tests...$(NC)"
	$(call check_venv)
	$(PYTHON_VENV) -m pytest tests/integration/ -m integration -v
	@echo "$(GREEN)✅ Integration tests completed$(NC)"

test-coverage: ## Run tests with coverage report
	@echo "$(YELLOW)🧪 Running tests with coverage...$(NC)"
	$(call check_venv)
	$(PYTHON_VENV) -m pytest tests/ --cov=src --cov-report=term-missing -v
	@echo "$(GREEN)✅ Coverage tests completed$(NC)"

lint: ## Basic code quality check
	@echo "$(YELLOW)🔍 Running basic lint check...$(NC)"
	$(call check_venv)
	@echo "$(BLUE)📝 Checking Python syntax...$(NC)"
	find src -name "*.py" -exec $(PYTHON_VENV) -m py_compile {} \;
	@echo "$(GREEN)✅ Syntax check completed$(NC)"

validate-aws: ## Validate AWS SSO session
	@echo "$(YELLOW)🔍 Validating AWS SSO session...$(NC)"
	$(call get_aws_account)
	@echo "$(GREEN)✅ AWS SSO session active$(NC)"

plan: ## Show deployment plan
	@echo "$(YELLOW)📋 Generating Terraform plan...$(NC)"
	@test -d terraform || (echo "$(RED)❌ Terraform directory not found$(NC)" && exit 1)
	$(call get_aws_account) && \
	cd terraform && terraform init && terraform plan -var="aws_account_id=$$AWS_ACCOUNT_ID"

deploy: ## Deploy AWS infrastructure
	@echo "$(YELLOW)☁️  Deploying AWS infrastructure...$(NC)"
	@test -d terraform || (echo "$(RED)❌ Terraform directory not found$(NC)" && exit 1)
	$(call get_aws_account) && \
	cd terraform && terraform init && terraform apply -var="aws_account_id=$$AWS_ACCOUNT_ID"
	@echo "$(GREEN)✅ Infrastructure deployed$(NC)"

status: ## Show infrastructure status
	@echo "$(YELLOW)📊 Infrastructure status...$(NC)"
	@test -d terraform || (echo "$(RED)❌ Terraform directory not found$(NC)" && exit 1)
	$(call get_aws_account) && cd terraform && terraform show

refresh: ## Refresh infrastructure state
	@echo "$(YELLOW)🔄 Refreshing Terraform state...$(NC)"
	@test -d terraform || (echo "$(RED)❌ Terraform directory not found$(NC)" && exit 1)
	$(call get_aws_account) && \
	cd terraform && terraform init && terraform refresh -var="aws_account_id=$$AWS_ACCOUNT_ID"
	@echo "$(GREEN)✅ State refreshed$(NC)"

destroy: ## Destroy AWS infrastructure
	@echo "$(RED)⚠️  WARNING: This will destroy ALL AWS resources!$(NC)"
	@read -p "Type 'yes' to confirm: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		$(call get_aws_account) && \
		cd terraform && terraform destroy -var="aws_account_id=$$AWS_ACCOUNT_ID"; \
		echo "$(GREEN)✅ Infrastructure destroyed$(NC)"; \
	else \
		echo "$(BLUE)❌ Cancelled$(NC)"; \
	fi

clean: ## Clean temporary files
	@echo "$(YELLOW)🧹 Cleaning...$(NC)"
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	find . -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Cleaned$(NC)"
