# Lambda Layer for Dependencies
resource "aws_lambda_layer_version" "python_dependencies" {
  filename   = "${path.module}/lambda_layer.zip"
  layer_name = "${var.project_name}-dependencies"

  compatible_runtimes = ["python3.9", "python3.10", "python3.11"]
  
  # Only rebuild when file changes
  source_code_hash = fileexists("${path.module}/lambda_layer.zip") ? filebase64sha256("${path.module}/lambda_layer.zip") : ""
}

# Scheduler Lambda Function
resource "aws_lambda_function" "scheduler" {
  filename         = "${path.module}/lambda_deployment.zip"
  function_name    = "${var.project_name}-scheduler"
  role            = aws_iam_role.lambda_role.arn
  handler         = "src.lambda.scheduler_handler.lambda_handler"
  runtime         = "python3.9"
  timeout         = 60
  memory_size     = 256

  # Calculate Hash if file exists
  source_code_hash = fileexists("${path.module}/lambda_deployment.zip") ? filebase64sha256("${path.module}/lambda_deployment.zip") : ""

  layers = [aws_lambda_layer_version.python_dependencies.arn]

  environment {
    variables = {
      CARBON_API_PROVIDER     = var.carbon_api_provider
      CARBON_THRESHOLD        = "400"
      PROJECT_NAME            = var.project_name
      ELECTRICITYMAP_API_KEY  = var.electricitymap_api_key
      DYNAMODB_TABLE          = aws_dynamodb_table.state.name
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_logs,
    aws_cloudwatch_log_group.lambda_scheduler,
  ]
}


# Hourly Aggregator Lambda Function
resource "aws_lambda_function" "hourly_aggregator" {
  filename         = "${path.module}/lambda_deployment.zip"
  function_name    = "${var.project_name}-hourly-aggregator"
  role             = aws_iam_role.lambda_role.arn
  handler          = "src.lambda.hourly_aggregator.lambda_handler"
  runtime          = "python3.9"
  timeout          = 60
  memory_size      = 256

  source_code_hash = fileexists("${path.module}/lambda_deployment.zip") ? filebase64sha256("${path.module}/lambda_deployment.zip") : ""

  layers = [aws_lambda_layer_version.python_dependencies.arn]

  environment {
    variables = {
      PROJECT_NAME          = var.project_name
      HOURLY_TABLE_NAME     = aws_dynamodb_table.hourly.name
      STATE_TABLE_NAME      = aws_dynamodb_table.state.name
      CARBON_API_PROVIDER   = var.carbon_api_provider
      ELECTRICITYMAP_API_KEY = var.electricitymap_api_key
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_logs,
    aws_cloudwatch_log_group.lambda_hourly_aggregator,
  ]
}

# CloudWatch Log Group for Aggregator
resource "aws_cloudwatch_log_group" "lambda_hourly_aggregator" {
  name              = "/aws/lambda/${var.project_name}-hourly-aggregator"
  retention_in_days = var.lambda_log_retention_days
}

# EventBridge Rule for hourly execution
resource "aws_cloudwatch_event_rule" "hourly_aggregator_rule" {
  name                = "${var.project_name}-hourly-aggregator-rule"
  description         = "Trigger hourly aggregator every hour"
  schedule_expression = "rate(1 hour)"
  state               = "ENABLED"
}

resource "aws_cloudwatch_event_target" "hourly_aggregator_target" {
  rule      = aws_cloudwatch_event_rule.hourly_aggregator_rule.name
  target_id = "HourlyAggregatorTarget"
  arn       = aws_lambda_function.hourly_aggregator.arn
}

resource "aws_lambda_permission" "hourly_aggregator_permission" {
  statement_id  = "AllowExecutionFromEventBridgeHourly"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.hourly_aggregator.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.hourly_aggregator_rule.arn
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "lambda_scheduler" {
  name              = "/aws/lambda/${var.project_name}-scheduler"
  retention_in_days = 7
}


# IAM Role Policy Attachment for CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# EventBridge Rule for Scheduler (daily at 8 AM UTC)
resource "aws_cloudwatch_event_rule" "scheduler_rule" {
  name                = "${var.project_name}-scheduler-rule"
  description         = "Trigger scheduler Lambda daily at 8 AM UTC"
  schedule_expression = "cron(0 8 * * ? *)"
  
  # Enable automatic scheduling for thesis research
  state = "ENABLED"
}

# EventBridge Targets
resource "aws_cloudwatch_event_target" "scheduler_target" {
  rule      = aws_cloudwatch_event_rule.scheduler_rule.name
  target_id = "SchedulerLambdaTarget"
  arn       = aws_lambda_function.scheduler.arn
}

# Lambda Permissions for EventBridge
resource "aws_lambda_permission" "scheduler_permission" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.scheduler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scheduler_rule.arn
}



# Outputs
output "scheduler_function_name" {
  value = aws_lambda_function.scheduler.function_name
}

output "scheduler_function_arn" {
  value = aws_lambda_function.scheduler.arn
}


output "hourly_aggregator_function_name" {
  value = aws_lambda_function.hourly_aggregator.function_name
}

output "hourly_aggregator_function_arn" {
  value = aws_lambda_function.hourly_aggregator.arn
}
