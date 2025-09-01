# Carbon-Aware FinOps - Streamlined Makefile
# Essential commands for efficient development and deployment

.PHONY: help setup dev test deploy run clean
.DEFAULT_GOAL := help

# Configuration
PYTHON := python3
VENV := venv
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
	@echo "$(BOLD)$(GREEN)🌱 Carbon-Aware FinOps - Essential Commands$(NC)"
	@echo "=================================================="
	@echo ""
	@echo "$(BOLD)🚀 Getting Started:$(NC)"
	@echo "  $(BLUE)make setup$(NC)        - Complete project setup (first time)"
	@echo "  $(BLUE)make dev$(NC)          - Setup development environment"
	@echo "  $(BLUE)make fresh-start$(NC)  - Complete reset + setup + deploy + run (testing)"
	@echo ""
	@echo "$(BOLD)💻 Development:$(NC)"
	@echo "  $(BLUE)make test$(NC)         - Run all tests and quality checks"
	@echo "  $(BLUE)make clean$(NC)        - Clean temporary files and caches"
	@echo "  $(BLUE)make reset$(NC)        - Complete project cleanup (⚠️  removes everything!)"
	@echo ""
	@echo "$(BOLD)☁️  Deployment:$(NC)"
	@echo "  $(BLUE)make deploy$(NC)       - Deploy complete infrastructure to AWS"
	@echo "  $(BLUE)make destroy$(NC)      - Destroy AWS infrastructure (⚠️  careful!)"
	@echo ""
	@echo "$(BOLD)🏃 Operations:$(NC)"
	@echo "  $(BLUE)make run$(NC)          - Run the complete carbon-aware system"
	@echo "  $(BLUE)make dashboard$(NC)    - Launch real-time dashboard"
	@echo "  $(BLUE)make status$(NC)       - Show system and infrastructure status"
	@echo ""
	@echo "$(BOLD)🔧 Advanced:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && !/help|setup|dev|test|deploy|run|clean|dashboard|status|destroy|reset|fresh-start/ {printf "  $(BLUE)%-12s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# 🚀 GETTING STARTED
setup: ## 🔧 Complete project setup (run this first!)
	@echo "$(BOLD)$(GREEN)🚀 Setting up Carbon-Aware FinOps Project$(NC)"
	@echo "=========================================="
	@echo "$(YELLOW)1/4 Creating virtual environment...$(NC)"
	@$(PYTHON) -m venv $(VENV)
	@./$(VENV)/bin/pip install --upgrade pip setuptools wheel
	@echo "$(YELLOW)2/4 Installing dependencies...$(NC)"
	@./$(VENV)/bin/pip install -r requirements.txt
	@./$(VENV)/bin/pip install -r requirements-dev.txt 2>/dev/null || echo "$(YELLOW)⚠️  Dev requirements not found, skipping$(NC)"
	@./$(VENV)/bin/pip install -e .
	@echo "$(YELLOW)3/4 Running quality checks...$(NC)"
	@$(MAKE) _quick-test
	@echo "$(YELLOW)4/4 Checking AWS connectivity...$(NC)"
	@aws sts get-caller-identity --profile $(AWS_PROFILE) >/dev/null 2>&1 && \
		echo "$(GREEN)✅ AWS connection successful$(NC)" || \
		echo "$(RED)⚠️  AWS not configured. Run: aws configure --profile $(AWS_PROFILE)$(NC)"
	@echo ""
	@echo "$(BOLD)$(GREEN)🎉 Setup complete!$(NC)"
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "  • Run '$(BOLD)make deploy$(NC)' to deploy infrastructure"
	@echo "  • Run '$(BOLD)make run$(NC)' to start the carbon-aware system"
	@echo "  • Run '$(BOLD)make dashboard$(NC)' to view real-time metrics"

dev: ## 💻 Setup development environment
	@echo "$(BOLD)$(YELLOW)💻 Development Environment Setup$(NC)"
	@echo "=================================="
	@$(MAKE) _ensure-venv
	@echo "$(YELLOW)Installing development tools...$(NC)"
	@./$(VENV)/bin/pip install -r requirements-dev.txt
	@./$(VENV)/bin/pip install -e .
	@echo "$(YELLOW)Formatting code...$(NC)"
	@./$(VENV)/bin/black src tests --line-length=120 --quiet
	@echo "$(YELLOW)Running quality checks...$(NC)"
	@$(MAKE) test
	@echo "$(GREEN)✅ Development environment ready!$(NC)"

# 💻 DEVELOPMENT
test: ## 🧪 Run comprehensive tests and quality checks
	@echo "$(BOLD)$(YELLOW)🧪 Running Quality Checks$(NC)"
	@echo "=========================="
	@$(MAKE) _ensure-venv
	@echo "$(YELLOW)1/4 Linting code...$(NC)"
	@./$(VENV)/bin/flake8 src --max-line-length=120 --extend-ignore=E203,W503 || (echo "$(RED)❌ Linting failed$(NC)" && exit 1)
	@echo "$(YELLOW)2/4 Type checking...$(NC)"
	@./$(VENV)/bin/mypy src --ignore-missing-imports || (echo "$(RED)❌ Type checking failed$(NC)" && exit 1)
	@echo "$(YELLOW)3/4 Running tests...$(NC)"
	@./$(VENV)/bin/pytest tests/ -v --tb=short || (echo "$(RED)❌ Tests failed$(NC)" && exit 1)
	@echo "$(YELLOW)4/4 Security scan...$(NC)"
	@./$(VENV)/bin/bandit -r src --quiet || echo "$(YELLOW)⚠️  Security warnings found$(NC)"
	@echo "$(GREEN)✅ All quality checks passed!$(NC)"

clean: ## 🧹 Clean temporary files and caches
	@echo "$(YELLOW)🧹 Cleaning project...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .mypy_cache htmlcov carbon_aware_finops.egg-info 2>/dev/null || true
	@find infrastructure/ -name "*.tfstate.backup" -delete 2>/dev/null || true
	@find . -name ".DS_Store" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

reset: ## 🔥 Complete project reset (removes everything!)
	@echo "$(BOLD)$(RED)🔥 COMPLETE PROJECT RESET$(NC)"
	@echo "=========================="
	@echo "$(RED)⚠️  This will remove:$(NC)"
	@echo "  • Virtual environment"
	@echo "  • All temporary/cache files"
	@echo "  • Terraform state and cache"
	@echo "  • Lambda zip files"
	@echo "  • Log files"
	@echo "  • All build artifacts"
	@echo ""
	@read -p "⚠️  Continue with complete reset? [y/N] " -r && \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(YELLOW)1/6 Removing virtual environment...$(NC)"; \
		rm -rf $(VENV) 2>/dev/null || true; \
		echo "$(YELLOW)2/6 Cleaning Python artifacts...$(NC)"; \
		find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true; \
		find . -type f -name "*.pyc" -delete 2>/dev/null || true; \
		find . -type f -name "*.pyo" -delete 2>/dev/null || true; \
		rm -rf .mypy_cache .pytest_cache htmlcov carbon_aware_finops.egg-info 2>/dev/null || true; \
		echo "$(YELLOW)3/6 Cleaning Terraform artifacts...$(NC)"; \
		rm -rf infrastructure/terraform/.terraform 2>/dev/null || true; \
		rm -rf infrastructure/terraform/.terraform.lock.hcl 2>/dev/null || true; \
		find infrastructure/ -name "*.tfstate*" -delete 2>/dev/null || true; \
		find infrastructure/ -name "terraform.tfplan*" -delete 2>/dev/null || true; \
		echo "$(YELLOW)4/6 Removing Lambda packages...$(NC)"; \
		find infrastructure/ -name "*.zip" -delete 2>/dev/null || true; \
		echo "$(YELLOW)5/6 Cleaning logs and temporary files...$(NC)"; \
		rm -rf logs/*.log 2>/dev/null || true; \
		find . -name ".DS_Store" -delete 2>/dev/null || true; \
		find . -name "*.tmp" -delete 2>/dev/null || true; \
		echo "$(YELLOW)6/6 Final cleanup...$(NC)"; \
		rm -rf OPTIMIZATION_REPORT.md 2>/dev/null || true; \
		echo ""; \
		echo "$(BOLD)$(GREEN)🎉 Complete reset finished!$(NC)"; \
		echo "$(BLUE)Project is now in pristine state$(NC)"; \
		echo "$(BLUE)Run 'make setup' to begin again$(NC)"; \
	else \
		echo "$(BLUE)❌ Reset cancelled$(NC)"; \
	fi

fresh-start: ## 🌟 Complete workflow: reset → setup → deploy → run (perfect for testing!)
	@echo "$(BOLD)$(GREEN)🌟 FRESH START - Complete Workflow$(NC)"
	@echo "===================================="
	@echo "$(BLUE)This will:$(NC)"
	@echo "  1. Reset the entire project"
	@echo "  2. Setup fresh environment"  
	@echo "  3. Deploy infrastructure to AWS"
	@echo "  4. Run the carbon-aware system"
	@echo ""
	@read -p "🚀 Start fresh workflow? [y/N] " -r && \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BOLD)$(YELLOW)Phase 1: Resetting project...$(NC)"; \
		$(MAKE) _silent-reset; \
		echo ""; \
		echo "$(BOLD)$(YELLOW)Phase 2: Setting up environment...$(NC)"; \
		$(MAKE) setup; \
		echo ""; \
		echo "$(BOLD)$(YELLOW)Phase 3: Deploying infrastructure...$(NC)"; \
		$(MAKE) deploy; \
		echo ""; \
		echo "$(BOLD)$(YELLOW)Phase 4: Running system...$(NC)"; \
		$(MAKE) run; \
		echo ""; \
		echo "$(BOLD)$(GREEN)🎉 FRESH START COMPLETE!$(NC)"; \
		echo "$(GREEN)Your Carbon-Aware FinOps system is ready!$(NC)"; \
		echo ""; \
		echo "$(BLUE)Next steps:$(NC)"; \
		echo "  • View dashboard: make dashboard"; \
		echo "  • Check status: make status"; \
		echo "  • View logs: make logs"; \
	else \
		echo "$(BLUE)❌ Fresh start cancelled$(NC)"; \
	fi

# ☁️ DEPLOYMENT
deploy: ## 🚀 Deploy complete infrastructure to AWS
	@echo "$(BOLD)$(GREEN)🚀 Deploying Carbon-Aware FinOps$(NC)"
	@echo "=================================="
	@$(MAKE) _ensure-venv
	@echo "$(YELLOW)1/4 Initializing Terraform...$(NC)"
	@cd infrastructure/terraform && terraform init -upgrade
	@echo "$(YELLOW)2/4 Building Lambda packages...$(NC)"
	@cd infrastructure/terraform && ./build_lambda.sh
	@echo "$(YELLOW)3/4 Deploying infrastructure...$(NC)"
	@cd infrastructure/terraform && terraform apply -var="aws_profile=$(AWS_PROFILE)" -var="aws_region=$(AWS_REGION)" -auto-approve
	@echo "$(YELLOW)4/4 Setting up secrets...$(NC)"
	@./$(VENV)/bin/python scripts/setup_secrets.py --aws-profile $(AWS_PROFILE) || echo "$(YELLOW)⚠️  Configure API secrets manually$(NC)"
	@echo ""
	@echo "$(BOLD)$(GREEN)🎉 Deployment complete!$(NC)"
	@echo "$(BLUE)Infrastructure deployed successfully$(NC)"
	@$(MAKE) status

destroy: ## ⚠️  Destroy AWS infrastructure
	@echo "$(BOLD)$(RED)⚠️  WARNING: This will destroy all AWS infrastructure!$(NC)"
	@read -p "Type 'yes' to confirm destruction: " confirm && \
	if [ "$$confirm" = "yes" ]; then \
		cd infrastructure/terraform && terraform destroy -var="aws_profile=$(AWS_PROFILE)" -var="aws_region=$(AWS_REGION)" -auto-approve && \
		echo "$(GREEN)✅ Infrastructure destroyed$(NC)"; \
	else \
		echo "$(BLUE)❌ Destruction cancelled$(NC)"; \
	fi

# 🏃 OPERATIONS
run: ## 🏃 Run the complete carbon-aware system
	@echo "$(BOLD)$(YELLOW)🏃 Running Carbon-Aware System$(NC)"
	@echo "==============================="
	@$(MAKE) _ensure-venv
	@echo "$(YELLOW)1/3 Collecting baseline data...$(NC)"
	@./$(VENV)/bin/python scripts/collect_baseline.py --profile $(AWS_PROFILE) || echo "$(YELLOW)⚠️  Baseline collection partial$(NC)"
	@echo "$(YELLOW)2/3 Running scheduler...$(NC)"
	@./$(VENV)/bin/python src/automation/shutdown_scheduler.py || echo "$(YELLOW)⚠️  Scheduler issues detected$(NC)"
	@echo "$(YELLOW)3/3 Running rightsizing analysis...$(NC)"
	@./$(VENV)/bin/python src/lambda/rightsizing_handler.py || echo "$(YELLOW)⚠️  Rightsizing issues detected$(NC)"
	@echo "$(GREEN)✅ System execution complete$(NC)"
	@echo "$(BLUE)💡 Launch dashboard: make dashboard$(NC)"

dashboard: ## 📊 Launch real-time dashboard
	@echo "$(BOLD)$(BLUE)📊 Starting Carbon-Aware Dashboard$(NC)"
	@echo "==================================="
	@$(MAKE) _ensure-venv
	@echo "$(BLUE)🌐 Dashboard will be available at: http://localhost:8050$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop the dashboard$(NC)"
	@./$(VENV)/bin/python src/reporting/realtime_dashboard.py

status: ## 📈 Show comprehensive system status
	@echo "$(BOLD)$(BLUE)📈 System Status$(NC)"
	@echo "================"
	@echo "$(BOLD)AWS Connection:$(NC)"
	@aws sts get-caller-identity --profile $(AWS_PROFILE) >/dev/null 2>&1 && \
		echo "  $(GREEN)✅ Connected$(NC)" || echo "  $(RED)❌ Not connected$(NC)"
	@echo "$(BOLD)Infrastructure:$(NC)"
	@cd infrastructure/terraform && terraform output -json 2>/dev/null | python3 -m json.tool 2>/dev/null >/dev/null && \
		echo "  $(GREEN)✅ Deployed$(NC)" || echo "  $(YELLOW)⚠️  Not deployed$(NC)"
	@echo "$(BOLD)Managed EC2 Instances:$(NC)"
	@aws ec2 describe-instances \
		--filters "Name=tag:Project,Values=carbon-aware-finops" \
		--query 'Reservations[*].Instances[*].[InstanceId,State.Name,InstanceType,Tags[?Key==`Name`].Value|[0]]' \
		--output table \
		--profile $(AWS_PROFILE) 2>/dev/null || echo "  $(YELLOW)⚠️  No instances found$(NC)"

# 🔧 ADVANCED COMMANDS
plan: ## 📋 Show Terraform deployment plan
	@$(MAKE) _ensure-venv
	@cd infrastructure/terraform && terraform init -upgrade
	@cd infrastructure/terraform && ./build_lambda.sh
	@cd infrastructure/terraform && terraform plan -var="aws_profile=$(AWS_PROFILE)" -var="aws_region=$(AWS_REGION)"

baseline: ## 📊 Collect AWS baseline data
	@$(MAKE) _ensure-venv
	@./$(VENV)/bin/python scripts/collect_baseline.py --profile $(AWS_PROFILE)

scheduler: ## ⏰ Run carbon-aware scheduler once
	@$(MAKE) _ensure-venv
	@./$(VENV)/bin/python src/automation/shutdown_scheduler.py

rightsizing: ## 📐 Run rightsizing analysis
	@$(MAKE) _ensure-venv
	@./$(VENV)/bin/python src/lambda/rightsizing_handler.py

logs: ## 📄 View recent Lambda logs
	@echo "$(YELLOW)Recent Lambda logs:$(NC)"
	@aws logs tail /aws/lambda/carbon-aware-finops-scheduler --since 1h --region $(AWS_REGION) --profile $(AWS_PROFILE) 2>/dev/null || echo "$(YELLOW)No scheduler logs$(NC)"
	@aws logs tail /aws/lambda/carbon-aware-finops-rightsizing --since 1h --region $(AWS_REGION) --profile $(AWS_PROFILE) 2>/dev/null || echo "$(YELLOW)No rightsizing logs$(NC)"

instances: ## 💻 List managed EC2 instances
	@aws ec2 describe-instances \
		--filters "Name=tag:Project,Values=carbon-aware-finops" \
		--query 'Reservations[*].Instances[*].[InstanceId,State.Name,InstanceType,Tags[?Key==`Schedule`].Value|[0],Tags[?Key==`Name`].Value|[0]]' \
		--output table \
		--profile $(AWS_PROFILE)

emergency-stop: ## 🚨 Emergency stop all managed instances
	@echo "$(RED)🚨 EMERGENCY STOP$(NC)"
	@read -p "Stop all managed instances? [y/N] " -r && \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		aws ec2 describe-instances \
			--filters "Name=tag:Project,Values=carbon-aware-finops" "Name=instance-state-name,Values=running" \
			--query 'Reservations[*].Instances[*].InstanceId' \
			--output text --profile $(AWS_PROFILE) | \
		xargs -r aws ec2 stop-instances --instance-ids --profile $(AWS_PROFILE) && \
		echo "$(GREEN)✅ Emergency stop complete$(NC)"; \
	fi

# Internal helper targets (not shown in help)
_ensure-venv:
	@test -d $(VENV) || (echo "$(RED)❌ Virtual environment not found. Run 'make setup' first.$(NC)" && exit 1)

_quick-test:
	@./$(VENV)/bin/flake8 src --max-line-length=120 --extend-ignore=E203,W503 --quiet || echo "$(YELLOW)⚠️  Linting issues$(NC)"
	@./$(VENV)/bin/pytest tests/ -x --quiet --tb=no 2>/dev/null || echo "$(YELLOW)⚠️  Some tests failing$(NC)"

_silent-reset:
	@echo "$(YELLOW)Removing virtual environment...$(NC)"
	@rm -rf $(VENV) 2>/dev/null || true
	@echo "$(YELLOW)Cleaning Python artifacts...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@rm -rf .mypy_cache .pytest_cache htmlcov carbon_aware_finops.egg-info 2>/dev/null || true
	@echo "$(YELLOW)Cleaning Terraform artifacts...$(NC)"
	@rm -rf infrastructure/terraform/.terraform 2>/dev/null || true
	@rm -rf infrastructure/terraform/.terraform.lock.hcl 2>/dev/null || true
	@find infrastructure/ -name "*.tfstate*" -delete 2>/dev/null || true
	@find infrastructure/ -name "terraform.tfplan*" -delete 2>/dev/null || true
	@echo "$(YELLOW)Removing Lambda packages...$(NC)"
	@find infrastructure/ -name "*.zip" -delete 2>/dev/null || true
	@echo "$(YELLOW)Final cleanup...$(NC)"
	@rm -rf logs/*.log 2>/dev/null || true
	@find . -name ".DS_Store" -delete 2>/dev/null || true
	@find . -name "*.tmp" -delete 2>/dev/null || true
	@rm -rf OPTIMIZATION_REPORT.md 2>/dev/null || true