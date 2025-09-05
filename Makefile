# Carbon-Aware FinOps - Essential Commands Only
# Streamlined Makefile with core functionality

.PHONY: help first-time-setup setup test cleanup reset deploy destroy run dashboard status emergency-stop logs instances
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
	@echo "$(BOLD)$(GREEN)🔍 Infrastructure Analysis & Optimization Tool$(NC)"
	@echo "=================================================="
	@echo "$(BLUE)Analysis-focused: Shows optimization potential, no automation$(NC)"
	@echo ""
	@echo "$(BOLD)🚀 Getting Started:$(NC)"
	@echo "  $(BLUE)make first-time-setup$(NC) - Complete first-time setup (recommended)"
	@echo "  $(BLUE)make setup$(NC)        - Project setup only (existing config)"
	@echo ""
	@echo "$(BOLD)💻 Development:$(NC)"
	@echo "  $(BLUE)make test$(NC)         - Run all tests and quality checks"
	@echo "  $(BLUE)make cleanup$(NC)      - Clean temporary files and caches"
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
	@echo "$(BOLD)🔧 Utilities:$(NC)"
	@echo "  $(BLUE)make emergency-stop$(NC) - 🚨 Emergency stop all managed instances"
	@echo "  $(BLUE)make logs$(NC)         - 📄 View recent Lambda logs"
	@echo "  $(BLUE)make instances$(NC)    - 💻 List managed EC2 instances"

# 🚀 GETTING STARTED
first-time-setup: ## 🚀 Complete first-time setup with automatic configuration
	@echo "$(BOLD)$(GREEN)🚀 Carbon-Aware FinOps First-Time Setup$(NC)"
	@echo "========================================"
	@echo ""
	@if [ ! -f "infrastructure/terraform/terraform.tfvars" ]; then \
		echo "$(YELLOW)1/4 Creating terraform.tfvars from example...$(NC)"; \
		cp infrastructure/terraform/terraform.tfvars.example infrastructure/terraform/terraform.tfvars; \
		echo ""; \
		echo "$(BOLD)$(RED)⚠️  CONFIGURATION REQUIRED$(NC)"; \
		echo "$(RED)Please edit infrastructure/terraform/terraform.tfvars with:$(NC)"; \
		echo "  • Your AWS Account ID (find in AWS console upper right)"; \
		echo "  • Your AWS Profile (usually your SSO profile name)"; \
		echo "  • Optional: API keys for enhanced carbon data"; \
		echo ""; \
		echo "$(BLUE)💡 Then run 'make first-time-setup' again to continue$(NC)"; \
		echo "$(BLUE)💡 Or run individual commands: make setup && make deploy$(NC)"; \
	else \
		echo "$(YELLOW)1/4 Configuration found, proceeding with setup...$(NC)"; \
		$(MAKE) setup; \
		echo "$(YELLOW)2/4 Deploying infrastructure...$(NC)"; \
		$(MAKE) deploy; \
		echo "$(YELLOW)3/4 Running initial analysis...$(NC)"; \
		$(MAKE) run; \
		echo "$(YELLOW)4/4 Setup complete!$(NC)"; \
		echo ""; \
		echo "$(BOLD)$(GREEN)🎉 First-Time Setup Complete!$(NC)"; \
		echo "================================"; \
		echo "$(BLUE)Your Carbon-Aware FinOps tool is ready!$(NC)"; \
		echo ""; \
		echo "$(BOLD)Next steps:$(NC)"; \
		echo "  • Run $(BOLD)make dashboard$(NC) to view analysis results"; \
		echo "  • Check $(BOLD)make status$(NC) for system health"; \
		echo "  • View $(BOLD)make instances$(NC) for test instances"; \
		echo ""; \
		echo "$(YELLOW)💡 The system analyzes instances hourly automatically$(NC)"; \
	fi
setup: ## 🔧 Project setup only (use 'make first-time-setup' for new installations)
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
		echo "$(RED)⚠️  AWS not configured. Run: aws sso login --sso-session $(AWS_PROFILE)$(NC)"
	@echo ""
	@echo "$(BOLD)$(GREEN)🎉 Setup complete!$(NC)"
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "  • Run '$(BOLD)make deploy$(NC)' to deploy infrastructure"
	@echo "  • Run '$(BOLD)make run$(NC)' to start the carbon-aware system"
	@echo "  • Run '$(BOLD)make dashboard$(NC)' to view real-time metrics"
	@echo "$(YELLOW)💡 For new installations, use '$(BOLD)make first-time-setup$(NC)' instead$(NC)"

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

cleanup: ## 🧹 Clean temporary files and caches
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
	@echo "$(YELLOW)4/4 Setting environment variables...$(NC)"
	@echo "$(BLUE)Set these environment variables for enhanced features:$(NC)"
	@echo "  export ELECTRICITYMAP_API_KEY='your-key'"
	@echo "  export WATTTIME_USERNAME='your-username'"
	@echo "  export WATTTIME_PASSWORD='your-password'"
	@echo ""
	@echo "$(BOLD)$(GREEN)🎉 Deployment complete!$(NC)"
	@echo "$(BLUE)Infrastructure deployed successfully$(NC)"
	@$(MAKE) status

destroy: ## 🧹 Complete cleanup of ALL AWS resources
	@echo "$(BOLD)$(RED)🧹 COMPREHENSIVE AWS CLEANUP$(NC)"
	@echo "$(BOLD)🔍 Checking current resources:$(NC)"
	@$(MAKE) --no-print-directory _check_resources
	@read -p "$(RED)Type 'CLEANUP' to permanently delete ALL resources: $(NC)" confirm && \
	if [ "$$confirm" = "CLEANUP" ]; then \
		echo "$(YELLOW)🚀 Using Terraform destroy for complete cleanup...$(NC)"; \
		cd infrastructure/terraform && terraform destroy -auto-approve; \
		cd ../..; \
		echo "$(YELLOW)🧹 Cleaning up any remaining orphaned resources...$(NC)"; \
		$(MAKE) --no-print-directory _cleanup_orphaned_resources; \
		echo "$(YELLOW)✅ Verifying cleanup completion...$(NC)"; \
		$(MAKE) --no-print-directory _verify_cleanup; \
	else \
		echo "$(RED)❌ Cleanup cancelled. Resources preserved.$(NC)"; \
	fi

# 🏃 OPERATIONS
run: ## 🏃 Run the complete carbon-aware system
	@echo "$(BOLD)$(YELLOW)🏃 Running Carbon-Aware System$(NC)"
	@echo "==============================="
	@$(MAKE) _ensure-venv
	@echo "$(YELLOW)1/3 Triggering Lambda scheduler...$(NC)"
	@aws lambda invoke --function-name carbon-aware-finops-carbon-scheduler --profile $(AWS_PROFILE) /tmp/lambda-response.json || echo "$(RED)⚠️  Lambda invocation failed$(NC)"
	@echo "$(YELLOW)2/3 Checking Lambda execution results...$(NC)"
	@cat /tmp/lambda-response.json 2>/dev/null || echo "$(YELLOW)⚠️  No response file$(NC)"
	@echo "$(YELLOW)3/3 System ready - Lambda runs automatically every hour$(NC)"
	@echo "$(GREEN)✅ System execution complete$(NC)"
	@echo "$(BLUE)💡 Launch dashboard: make dashboard$(NC)"

dashboard: ## 📊 Launch Infrastructure Analysis & Optimization Dashboard
	@echo "$(BOLD)$(BLUE)📊 Starting Infrastructure Analysis Dashboard$(NC)"
	@echo "=============================================="
	@echo "$(BLUE)🌐 Dashboard will be available at: http://localhost:8051$(NC)"
	@echo "$(BLUE)🎯 Focus: Analysis & optimization potential (no automation)$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop the dashboard$(NC)"
	@$(MAKE) _ensure-venv
	@./$(VENV)/bin/python src/reporting/optimization_analysis_dashboard.py

dashboard-legacy: ## 📊 Launch legacy dashboard (deprecated)
	@echo "$(BOLD)$(YELLOW)📊 Starting Legacy Dashboard$(NC)"
	@echo "================================="
	@echo "$(YELLOW)⚠️  This is the old dashboard - use 'make dashboard' for current version$(NC)"
	@echo "$(BLUE)🌐 Dashboard will be available at: http://localhost:8050$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop the dashboard$(NC)"
	@$(MAKE) _ensure-venv
	@./$(VENV)/bin/python src/reporting/thesis_dashboard_OBSOLETE.py

status: ## 📊 Show comprehensive system and infrastructure status
	@echo "$(BOLD)$(BLUE)📊 Carbon-Aware FinOps System Status$(NC)"
	@echo "====================================="
	@echo ""
	@echo "$(BOLD)🏗️  Infrastructure:$(NC)"
	@$(MAKE) --no-print-directory _infrastructure_status
	@echo ""
	@echo "$(BOLD)💻 EC2 Instances:$(NC)"
	@$(MAKE) --no-print-directory _instance_status
	@echo ""
	@echo "$(BOLD)⚡ Lambda Functions:$(NC)"
	@$(MAKE) --no-print-directory _lambda_status

# 🔧 UTILITIES
emergency-stop: ## 🚨 Emergency stop all managed instances
	@echo "$(BOLD)$(RED)🚨 EMERGENCY STOP$(NC)"
	@echo "=================="
	@echo "$(RED)⚠️  This will immediately stop ALL managed instances$(NC)"
	@echo ""
	@read -p "$(RED)Continue with emergency stop? [y/N] $(NC)" -r && \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(YELLOW)Stopping all instances...$(NC)"; \
		aws ec2 stop-instances \
			--instance-ids $$(aws ec2 describe-instances \
				--filters "Name=tag:Project,Values=carbon-aware-finops" "Name=instance-state-name,Values=running" \
				--query 'Reservations[*].Instances[*].InstanceId' \
				--output text \
				--profile $(AWS_PROFILE) 2>/dev/null || echo "") \
			--profile $(AWS_PROFILE) 2>/dev/null && \
		echo "$(GREEN)✅ Emergency stop completed$(NC)" || \
		echo "$(YELLOW)ℹ️  No running instances found$(NC)"; \
	else \
		echo "$(BLUE)❌ Emergency stop cancelled$(NC)"; \
	fi

logs: ## 📄 View recent Lambda function logs
	@echo "$(BOLD)$(BLUE)📄 Recent Lambda Logs$(NC)"
	@echo "====================="
	@echo "$(YELLOW)Scheduler Lambda logs:$(NC)"
	@aws logs tail /aws/lambda/carbon-aware-finops-carbon-scheduler --since 1h --profile $(AWS_PROFILE) 2>/dev/null || echo "$(RED)No scheduler logs found$(NC)"


instances: ## 💻 List all managed EC2 instances with their purposes
	@echo "$(BOLD)$(BLUE)💻 Managed EC2 Instances$(NC)"
	@echo "========================"
	@echo "$(YELLOW)Instances with their roles and purposes:$(NC)"
	@aws ec2 describe-instances \
		--filters "Name=tag:Project,Values=carbon-aware-finops" \
		--query 'Reservations[*].Instances[*].[InstanceId,InstanceType,State.Name,Tags[?Key==`Name`].Value|[0],Tags[?Key==`Purpose`].Value|[0],Tags[?Key==`InstanceRole`].Value|[0]]' \
		--output table \
		--profile $(AWS_PROFILE) 2>/dev/null || echo "$(RED)No instances found$(NC)"

# 🔧 INTERNAL HELPERS
_ensure-venv:
	@test -d $(VENV) || (echo "$(RED)❌ Virtual environment not found. Run 'make setup' first$(NC)" && exit 1)

_quick-test:
	@./$(VENV)/bin/flake8 src --max-line-length=120 --extend-ignore=E203,W503 --quiet || echo "$(YELLOW)⚠️  Code style issues found$(NC)"
	@./$(VENV)/bin/mypy src --ignore-missing-imports --quiet || echo "$(YELLOW)⚠️  Type checking issues found$(NC)"

_check_resources:
	@echo "$(YELLOW)Checking current AWS resources...$(NC)"
	@INSTANCES=$$(aws ec2 describe-instances --filters "Name=tag:Project,Values=carbon-aware-finops" --query 'length(Reservations[*].Instances[*])' --output text --profile $(AWS_PROFILE) 2>/dev/null || echo "0"); \
	LAMBDAS=$$(aws lambda list-functions --query 'length(Functions[?contains(FunctionName, `carbon-aware-finops`)])' --output text --profile $(AWS_PROFILE) 2>/dev/null || echo "0"); \
	TABLES=$$(aws dynamodb list-tables --query 'length(TableNames[?contains(@, `carbon-aware-finops`)])' --output text --profile $(AWS_PROFILE) 2>/dev/null || echo "0"); \
	echo "  • EC2 Instances: $$INSTANCES"; \
	echo "  • Lambda Functions: $$LAMBDAS"; \
	echo "  • DynamoDB Tables: $$TABLES"

_cleanup_orphaned_resources:
	@echo "$(YELLOW)Cleaning orphaned Lambda functions...$(NC)"
	@aws lambda list-functions --query 'Functions[?contains(FunctionName, `carbon-aware-finops`)].FunctionName' --output text --profile $(AWS_PROFILE) 2>/dev/null | \
	while read -r func; do \
		if [ -n "$$func" ]; then \
			aws lambda delete-function --function-name "$$func" --profile $(AWS_PROFILE) 2>/dev/null || true; \
		fi; \
	done

_verify_cleanup:
	@echo "$(BOLD)🔍 FINAL VERIFICATION - Checking for remaining resources:$(NC)"
	@REMAINING=0; \
	INSTANCES=$$(aws ec2 describe-instances --filters "Name=tag:Project,Values=carbon-aware-finops" --query 'length(Reservations[*].Instances[*])' --output text --profile $(AWS_PROFILE) 2>/dev/null || echo "0"); \
	LAMBDAS=$$(aws lambda list-functions --query 'length(Functions[?contains(FunctionName, `carbon-aware-finops`)])' --output text --profile $(AWS_PROFILE) 2>/dev/null || echo "0"); \
	TABLES=$$(aws dynamodb list-tables --query 'length(TableNames[?contains(@, `carbon-aware-finops`)])' --output text --profile $(AWS_PROFILE) 2>/dev/null || echo "0"); \
	REMAINING=$$(($$INSTANCES + $$LAMBDAS + $$TABLES)); \
	if [ "$$REMAINING" = "0" ]; then \
		echo "$(GREEN)✅ VERIFICATION PASSED: All resources successfully removed!$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Some resources remain: EC2($$INSTANCES), Lambda($$LAMBDAS), DynamoDB($$TABLES)$(NC)"; \
	fi

_infrastructure_status:
	@aws sts get-caller-identity --query 'Account' --output text --profile $(AWS_PROFILE) 2>/dev/null && \
		echo "  ✅ AWS Connection: Active" || \
		echo "  ❌ AWS Connection: Failed"
	@cd infrastructure/terraform && terraform show -json 2>/dev/null | jq -r '.values.root_module.resources | length' 2>/dev/null | \
		xargs -I {} echo "  📊 Terraform Resources: {}" || \
		echo "  ⚠️  Terraform: Not initialized"

_instance_status:
	@RUNNING=$$(aws ec2 describe-instances --filters "Name=tag:Project,Values=carbon-aware-finops" "Name=instance-state-name,Values=running" --query 'length(Reservations[*].Instances[*])' --output text --profile $(AWS_PROFILE) 2>/dev/null || echo "0"); \
	STOPPED=$$(aws ec2 describe-instances --filters "Name=tag:Project,Values=carbon-aware-finops" "Name=instance-state-name,Values=stopped" --query 'length(Reservations[*].Instances[*])' --output text --profile $(AWS_PROFILE) 2>/dev/null || echo "0"); \
	echo "  🟢 Running: $$RUNNING  🔴 Stopped: $$STOPPED"

_lambda_status:
	@SCHEDULER_STATUS=$$(aws lambda get-function --function-name carbon-aware-finops-carbon-scheduler --query 'Configuration.State' --output text --profile $(AWS_PROFILE) 2>/dev/null || echo "NotFound"); \
	echo "  ⚡ Scheduler: $$SCHEDULER_STATUS"
