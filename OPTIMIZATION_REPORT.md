# Carbon-Aware FinOps Project Optimization Report

## 🔍 Unused Imports
**/Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/reporting/realtime_dashboard.py:**
  - pandas
  - plotly.graph_objects

**/Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/cost/aws_cost_client.py:**
  - pandas

**/Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/utils/logging_config.py:**
  - logging.handlers

## 📦 Large Files (>1MB)
  - /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../infrastructure/terraform/.terraform/providers/registry.terraform.io/hashicorp/aws/5.100.0/darwin_arm64/terraform-provider-aws_v5.100.0_x5 (648.4 MB)
  - /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../infrastructure/terraform/lambda_layer.zip (15.0 MB)
  - /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../.mypy_cache/3.13/numpy/__init__.data.json (5.7 MB)
  - /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../.mypy_cache/3.13/boto3/session.data.json (2.5 MB)
  - /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../.mypy_cache/3.13/boto3/__init__.data.json (2.4 MB)
  - /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../.mypy_cache/3.13/builtins.data.json (1.9 MB)
  - /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../.mypy_cache/3.9/builtins.data.json (1.7 MB)
  - /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../.mypy_cache/3.13/numpy/_core/fromnumeric.data.json (1.1 MB)

## 🔄 Potential Code Duplicates
  - Similar functions 'main' in: /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/reporting/realtime_dashboard.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/lambda/rightsizing_handler.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/automation/shutdown_scheduler.py
  - Similar functions 'init' in: /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/reporting/realtime_dashboard.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/reporting/realtime_dashboard.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/carbon/carbon_api_client.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/carbon/carbon_api_client.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/carbon/carbon_api_client.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/cost/aws_cost_client.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/utils/secrets_manager.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/utils/retry_handler.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/lambda/rightsizing_handler.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/automation/instance_manager.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/automation/shutdown_scheduler.py
  - Similar functions 'postinit' in: /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/config/settings.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/config/settings.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/config/settings.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/config/settings.py
  - Similar functions 'getcurrentintensity' in: /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/carbon/carbon_api_client.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/carbon/carbon_api_client.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/carbon/carbon_api_client.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/carbon/carbon_api_client.py
  - Similar functions 'getforecast' in: /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/carbon/carbon_api_client.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/carbon/carbon_api_client.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/carbon/carbon_api_client.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/carbon/carbon_api_client.py
  - Similar functions 'getfallbackintensity' in: /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/carbon/carbon_api_client.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/carbon/carbon_api_client.py
  - Similar functions 'getfallbackforecast' in: /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/carbon/carbon_api_client.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/carbon/carbon_api_client.py
  - Similar functions 'getsecret' in: /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/utils/secrets_manager.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/utils/secrets_manager.py
  - Similar functions 'lambdahandler' in: /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/lambda/rightsizing_handler.py, /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local/scripts/../src/lambda/scheduler_handler.py

## ✅ Code Quality
  - Flake8 status: ❌ Issues found
  - MyPy status: ✅ Pass

## 💡 Recommendations
1. **Remove unused imports** to reduce file size and improve clarity
2. **Review large files** for potential optimization opportunities
3. **Check for duplicate code** and consider refactoring
4. **Update dependency versions** for security and performance
5. **Run code quality tools** regularly as part of CI/CD