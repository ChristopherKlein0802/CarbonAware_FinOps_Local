# Carbon-Aware FinOps - Bachelor Thesis
# Professional Makefile for Clean Architecture

.PHONY: help setup dashboard deploy status destroy test clean streamlit
.DEFAULT_GOAL := help

# Configuration
PYTHON := python3
VENV := venv
AWS_PROFILE := carbon-finops-sandbox
AWS_REGION := eu-central-1
STREAMLIT_PORT := 8501

# Colors
GREEN := \033[0;32m
YELLOW := \033[1;33m  
BLUE := \033[0;34m
BOLD := \033[1m
NC := \033[0m

help: ## 📋 Show deployment commands
	@echo "$(BOLD)$(GREEN)🎓 Carbon-Aware FinOps Dashboard - Bachelor Thesis$(NC)"
	@echo "=================================================="
	@echo "$(BLUE)Deployment-focused commands for Bachelor thesis$(NC)"
	@echo ""
	@echo "$(BOLD)🚀 Quick Start:$(NC)"
	@echo "  $(BLUE)make setup$(NC)     - Setup environment & dependencies"
	@echo "  $(BLUE)make streamlit$(NC) - 📊 Launch clean Streamlit dashboard"
	@echo "  $(BLUE)make deploy$(NC)    - ☁️  Deploy AWS test instances"
	@echo ""
	@echo "$(BOLD)📊 Dashboard Development:$(NC)"
	@echo "  $(BLUE)make streamlit$(NC)              - Clean Streamlit dashboard (recommended)"
	@echo "  $(BLUE)python run_clean_dashboard.py$(NC) - Professional launcher with validation"
	@echo "  $(BLUE)make health$(NC)                 - Check dashboard health"
	@echo ""
	@echo "$(BOLD)📊 Dashboard Options:$(NC)"
	@echo "  $(BLUE)make streamlit$(NC) - Clean Streamlit dashboard (Port $(STREAMLIT_PORT))"
	@echo "  $(BLUE)make dashboard$(NC) - Legacy dashboard (fallback)"
	@echo "  $(BLUE)make test$(NC)      - Test API integrations"
	@echo ""  
	@echo "$(BOLD)☁️  AWS Infrastructure:$(NC)"
	@echo "  $(BLUE)make deploy$(NC)    - Deploy 4 test instances for analysis"
	@echo "  $(BLUE)make status$(NC)    - Show current infrastructure status"
	@echo "  $(BLUE)make destroy$(NC)   - Remove all AWS resources (⚠️  careful!)"
	@echo ""
	@echo "$(BOLD)🔧 Utilities:$(NC)"
	@echo "  $(BLUE)make clean$(NC)     - Clean temporary files"
	@echo "  $(BLUE)make dev$(NC)       - Quick development start (python run.py dev)"
	@echo "  $(BLUE)make demo$(NC)      - Demo mode for presentations"
	@echo "  $(BLUE)make health$(NC)    - Check dashboard health"

setup: ## 🔧 Setup environment
	@echo "$(BOLD)$(GREEN)🔧 Setting up Carbon-Aware FinOps environment$(NC)"
	@echo "=============================================="
	@echo "$(YELLOW)Creating Python virtual environment...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		$(PYTHON) -m venv $(VENV) && echo "$(GREEN)✅ Virtual environment created$(NC)"; \
	else \
		echo "$(GREEN)✅ Virtual environment exists$(NC)"; \
	fi
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	@./$(VENV)/bin/pip install --upgrade pip setuptools wheel > /dev/null
	@./$(VENV)/bin/pip install -r requirements.txt > /dev/null && echo "$(GREEN)✅ Dependencies installed$(NC)"
	@echo "$(YELLOW)Checking API configuration...$(NC)"
	@if [ ! -f ".env" ]; then \
		echo "$(YELLOW)⚠️  Create .env file from .env.example for API keys$(NC)"; \
	else \
		echo "$(GREEN)✅ .env file found$(NC)"; \
	fi
	@if [ -f ".env" ]; then \
		source .env && $(MAKE) test > /dev/null 2>&1 && echo "$(GREEN)✅ API connections working$(NC)" || echo "$(YELLOW)⚠️  Configure API keys in .env$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Create .env file from .env.example$(NC)"; \
	fi
	@echo ""
	@echo "$(BOLD)$(GREEN)🎉 Setup complete! Run 'make streamlit' to start$(NC)"

streamlit: ## 📊 Launch Clean Streamlit Dashboard (Recommended)
	@echo "$(BOLD)$(GREEN)📊 Launching Clean Streamlit Dashboard$(NC)"
	@echo "============================================="
	@echo "$(BLUE)🎓 Bachelor Thesis Tool: Professional Clean Architecture$(NC)"
	@echo "$(BLUE)📊 Dashboard URL: http://127.0.0.1:$(STREAMLIT_PORT)$(NC)"
	@echo "$(BLUE)🇩🇪 German Grid Focus: Real ElectricityMap API data$(NC)"
	@echo "$(BLUE)🔬 APIs: ElectricityMap + Boavizta + AWS Cost Explorer$(NC)"
	@echo "$(BLUE)Press Ctrl+C to stop$(NC)"
	@echo ""
	@if [ -f ".env" ]; then \
		source .env; \
	fi && \
	./$(VENV)/bin/streamlit run src/app.py --server.port $(STREAMLIT_PORT) --server.headless false

dashboard: ## 📊 Launch Legacy Dashboard (Fallback)
	@echo "$(YELLOW)⚠️  Legacy Dashboard Launch$(NC)"
	@echo "$(BLUE)Recommended: Use 'make streamlit' for clean architecture$(NC)"
	@echo ""
	@echo "$(BOLD)$(GREEN)📊 Launching Legacy Dashboard$(NC)"
	@echo "======================================"
	@if [ -f ".env" ]; then \
		source .env; \
	fi && \
	./$(VENV)/bin/python3 -m dashboard.dashboard_main

deploy: ## ☁️  Deploy AWS test instances
	@echo "$(BOLD)$(GREEN)☁️  Deploying AWS Infrastructure$(NC)"
	@echo "=================================="
	@echo "$(YELLOW)Deploying 4 test instances for thesis validation...$(NC)"
	@AWS_ACCOUNT_ID=$$(aws sts get-caller-identity --profile $(AWS_PROFILE) --query 'Account' --output text) && \
	cd terraform && \
		terraform init && \
		terraform apply -auto-approve \
			-var="aws_account_id=$$AWS_ACCOUNT_ID" \
			-var="aws_profile=$(AWS_PROFILE)" \
			-var="aws_region=$(AWS_REGION)"
	@echo "$(GREEN)✅ AWS deployment complete!$(NC)"
	@echo "Data will appear in dashboard within 60 seconds"
	@$(MAKE) status

status: ## 📊 Show infrastructure status
	@echo "$(BOLD)$(GREEN)📊 Infrastructure Status$(NC)"
	@echo "========================="
	@echo "$(YELLOW)AWS Profile:$(NC) $(AWS_PROFILE)"
	@echo "$(YELLOW)AWS Region:$(NC) $(AWS_REGION)"
	@echo ""
	@aws ec2 describe-instances --profile $(AWS_PROFILE) --region $(AWS_REGION) \
		--filters "Name=tag:Project,Values=carbon-aware-finops" \
		--query 'Reservations[].Instances[].[InstanceId,InstanceType,State.Name,Tags[?Key==`Name`].Value|[0]]' \
		--output table || echo "$(YELLOW)⚠️  No instances found or AWS access issue$(NC)"

destroy: ## 🗑️  Destroy AWS infrastructure
	@echo "$(BOLD)$(YELLOW)⚠️  Destroying AWS Infrastructure$(NC)"
	@echo "==================================="
	@echo "$(YELLOW)This will remove ALL AWS resources created by this project!$(NC)"
	@read -p "Are you sure? Type 'yes' to continue: " confirm && [ "$$confirm" = "yes" ] || { echo "Cancelled"; exit 1; }
	@AWS_ACCOUNT_ID=$$(aws sts get-caller-identity --profile $(AWS_PROFILE) --query 'Account' --output text) && \
	cd terraform && terraform destroy -auto-approve \
		-var="aws_account_id=$$AWS_ACCOUNT_ID" \
		-var="aws_profile=$(AWS_PROFILE)" \
		-var="aws_region=$(AWS_REGION)"
	@echo "$(GREEN)✅ AWS resources destroyed$(NC)"

test: ## 🧪 Test API integrations (Clean Architecture)
	@echo "$(BOLD)$(GREEN)🧪 Testing API Integrations - Clean Architecture$(NC)"
	@echo "================================================="
	@echo "$(YELLOW)Testing Boavizta API (hardware power data)...$(NC)"
	@./$(VENV)/bin/python3 -c "from src.api_client import unified_api_client; result = unified_api_client.get_power_consumption('t3.medium'); print(f'✅ Boavizta: {result.avg_power_watts:.1f}W' if result else '❌ Boavizta failed')" 2>/dev/null
	@echo "$(YELLOW)Testing ElectricityMap API (carbon intensity)...$(NC)"
	@if [ -f ".env" ]; then \
		source .env && ./$(VENV)/bin/python3 -c "from src.api_client import unified_api_client; result = unified_api_client.get_current_carbon_intensity('eu-central-1'); print(f'✅ ElectricityMap: {result.value}g CO2/kWh' if result and result.value > 0 else '⚠️  ElectricityMap: Check API key')" 2>/dev/null; \
	else \
		echo "⚠️  ElectricityMap: Create .env file"; \
	fi
	@echo "$(YELLOW)Testing AWS Cost Explorer API...$(NC)"
	@if [ -f ".env" ]; then \
		source .env && ./$(VENV)/bin/python3 -c "from src.api_client import unified_api_client; result = unified_api_client.get_monthly_costs(); print('✅ AWS Cost Explorer: $$' + str(round(result.monthly_cost_usd, 2)) + ' USD' if result and result.monthly_cost_usd > 0 else '⚠️  AWS: Check credentials')" || echo "⚠️  AWS Cost Explorer: Check credentials"; \
	else \
		./$(VENV)/bin/python3 -c "from src.api_client import unified_api_client; result = unified_api_client.get_monthly_costs(); print('✅ AWS Cost Explorer: $$' + str(round(result.monthly_cost_usd, 2)) + ' USD' if result and result.monthly_cost_usd > 0 else '⚠️  AWS: Check credentials')" || echo "⚠️  AWS Cost Explorer: Check credentials"; \
	fi
	@echo "$(YELLOW)Testing Clean Architecture Health Check...$(NC)"
	@if [ -f ".env" ]; then \
		source .env && ./$(VENV)/bin/python3 -c "from src.health_monitor import health_check_manager; result = health_check_manager.quick_health_check(); print('✅ Clean Architecture Health Check passed' if result else '⚠️  Some APIs have issues')" 2>/dev/null; \
	else \
		./$(VENV)/bin/python3 -c "from src.health_monitor import health_check_manager; result = health_check_manager.quick_health_check(); print('✅ Clean Architecture Health Check passed' if result else '⚠️  Some APIs have issues')" 2>/dev/null; \
	fi

clean: ## 🧹 Clean temporary files
	@echo "$(BOLD)$(GREEN)🧹 Cleaning temporary files$(NC)"
	@echo "============================"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache/ build/ dist/ 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

# New Hybrid Integration Targets
dev: ## 🚀 Quick development start (recommended)
	@echo "$(BOLD)$(GREEN)🚀 Starting Development Mode$(NC)"
	@echo "=============================="
	@echo "$(BLUE)Using Python run.py for fast development$(NC)"
	@$(PYTHON) run.py dev

demo: ## 🎓 Demo mode for Bachelor Thesis presentations
	@echo "$(BOLD)$(GREEN)🎓 Starting Demo Mode$(NC)"
	@echo "========================="
	@echo "$(BLUE)Optimized for Bachelor Thesis presentations$(NC)"
	@$(PYTHON) run.py demo

health: ## 🏥 Check dashboard health status
	@echo "$(BOLD)$(GREEN)🏥 Dashboard Health Check$(NC)"
	@echo "=========================="
	@$(PYTHON) status.py

quick: ## ⚡ Super quick start (setup + dev)
	@echo "$(BOLD)$(GREEN)⚡ Quick Start$(NC)"
	@echo "==============="
	@make setup
	@echo ""
	@make dev