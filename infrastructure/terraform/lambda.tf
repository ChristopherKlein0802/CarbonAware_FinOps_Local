# Lambda Layer for Dependencies
resource "aws_lambda_layer_version" "python_dependencies" {
  filename   = "${path.module}/lambda_layer.zip"
  layer_name = "${var.project_name}-dependencies"

  compatible_runtimes = ["python3.9", "python3.10", "python3.11"]
  
  # Only rebuild when file changes
  source_code_hash = fileexists("${path.module}/lambda_layer.zip") ? filebase64sha256("${path.module}/lambda_layer.zip") : ""
}

# Infrastructure Analysis Lambda Function - Main thesis component  
resource "aws_lambda_function" "carbon_scheduler" {
  filename         = "${path.module}/lambda_deployment.zip"
  function_name    = "${local.project_name}-infrastructure-analyzer"
  role            = aws_iam_role.lambda_role.arn
  handler         = "scheduler_handler.lambda_handler"
  runtime         = "python3.9"
  timeout         = 300  # 5 minutes for Cost Explorer API calls
  memory_size     = 512  # More memory for data processing

  source_code_hash = fileexists("${path.module}/lambda_deployment.zip") ? filebase64sha256("${path.module}/lambda_deployment.zip") : ""

  layers = [aws_lambda_layer_version.python_dependencies.arn]

  environment {
    variables = {
      CARBON_API_PROVIDER     = var.carbon_api_provider
      CARBON_THRESHOLD        = "400"  # gCO2/kWh threshold
      PROJECT_NAME            = local.project_name
      ELECTRICITYMAP_API_KEY  = var.electricitymap_api_key
      WATTTIME_USERNAME      = var.watttime_username
      WATTTIME_PASSWORD      = var.watttime_password
      DYNAMODB_RESULTS_TABLE = aws_dynamodb_table.results.name
      DEPLOYMENT_MODE         = var.deployment_mode
      ANALYZE_ALL_INSTANCES   = var.analyze_all_instances ? "true" : "false"
      # AWS_REGION is automatically provided by Lambda runtime
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_logs,
    aws_cloudwatch_log_group.lambda_scheduler,
  ]
}



# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_scheduler" {
  name              = "/aws/lambda/${local.project_name}-infrastructure-analyzer"
  retention_in_days = 7
}


# IAM Role Policy Attachment for CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# EventBridge Rule - Runs every hour for continuous analysis
resource "aws_cloudwatch_event_rule" "scheduler_rule" {
  name                = "${local.project_name}-infrastructure-analyzer-rule"
  description         = "Trigger infrastructure analysis every hour for optimization potential calculation"
  schedule_expression = "rate(1 hour)"  # Every hour for thesis data collection
  
  # Enable automatic analysis for thesis research
  state = "ENABLED"
}

# EventBridge Target
resource "aws_cloudwatch_event_target" "scheduler_target" {
  rule      = aws_cloudwatch_event_rule.scheduler_rule.name
  target_id = "CarbonSchedulerTarget"
  arn       = aws_lambda_function.carbon_scheduler.arn
}

# Lambda Permission for EventBridge
resource "aws_lambda_permission" "scheduler_permission" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.carbon_scheduler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scheduler_rule.arn
}



# Outputs
output "carbon_scheduler_function_name" {
  value = aws_lambda_function.carbon_scheduler.function_name
}

output "carbon_scheduler_function_arn" {
  value = aws_lambda_function.carbon_scheduler.arn
}
