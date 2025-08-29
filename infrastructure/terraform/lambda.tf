# Lambda Layer for Dependencies
resource "aws_lambda_layer_version" "python_dependencies" {
  filename   = "${path.module}/lambda_layer.zip"
  layer_name = "${var.project_name}-dependencies"

  compatible_runtimes = ["python3.9", "python3.10", "python3.11"]
  
  # Nur neu bauen wenn sich die Datei ändert
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

# Rightsizing Lambda Function
resource "aws_lambda_function" "rightsizing" {
  filename         = "${path.module}/lambda_deployment.zip"
  function_name    = "${var.project_name}-rightsizing"
  role            = aws_iam_role.lambda_role.arn
  handler         = "src.lambda.rightsizing_handler.lambda_handler"
  runtime         = "python3.9"
  timeout         = 300
  memory_size     = 512

  # Calculate Hash if file exists
  source_code_hash = fileexists("${path.module}/lambda_deployment.zip") ? filebase64sha256("${path.module}/lambda_deployment.zip") : ""

  layers = [aws_lambda_layer_version.python_dependencies.arn]

  environment {
    variables = {
      PROJECT_NAME   = var.project_name
      DYNAMODB_TABLE = aws_dynamodb_table.state.name
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_logs,
    aws_cloudwatch_log_group.lambda_rightsizing,
  ]
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "lambda_scheduler" {
  name              = "/aws/lambda/${var.project_name}-scheduler"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "lambda_rightsizing" {
  name              = "/aws/lambda/${var.project_name}-rightsizing"
  retention_in_days = 7
}

# IAM Role Policy Attachment for CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# EventBridge Rule for Scheduler (every 15 minutes)
# FIX: state anstatt is_enabled verwenden
resource "aws_cloudwatch_event_rule" "scheduler_rule" {
  name                = "${var.project_name}-scheduler-rule"
  description         = "Trigger scheduler Lambda every 15 minutes"
  schedule_expression = "rate(15 minutes)"
  
  # Start disabled, enable after testing
  state = "DISABLED"  # FIX: Changed from is_enabled to state
}

# EventBridge Rule for Rightsizing (daily)
# FIX: state anstatt is_enabled verwenden
resource "aws_cloudwatch_event_rule" "rightsizing_rule" {
  name                = "${var.project_name}-rightsizing-rule"
  description         = "Trigger rightsizing analysis daily"
  schedule_expression = "cron(0 2 * * ? *)"  # 2 AM UTC daily
  
  # Start disabled, enable after testing
  state = "DISABLED"  # FIX: Changed from is_enabled to state
}

# EventBridge Targets
resource "aws_cloudwatch_event_target" "scheduler_target" {
  rule      = aws_cloudwatch_event_rule.scheduler_rule.name
  target_id = "SchedulerLambdaTarget"
  arn       = aws_lambda_function.scheduler.arn
}

resource "aws_cloudwatch_event_target" "rightsizing_target" {
  rule      = aws_cloudwatch_event_rule.rightsizing_rule.name
  target_id = "RightsizingLambdaTarget"
  arn       = aws_lambda_function.rightsizing.arn
}

# Lambda Permissions for EventBridge
resource "aws_lambda_permission" "scheduler_permission" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.scheduler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scheduler_rule.arn
}

resource "aws_lambda_permission" "rightsizing_permission" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"  
  function_name = aws_lambda_function.rightsizing.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.rightsizing_rule.arn
}

# SNS Topic for Notifications
resource "aws_sns_topic" "notifications" {
  name = "${var.project_name}-notifications"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.notifications.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

# Outputs
output "scheduler_function_name" {
  value = aws_lambda_function.scheduler.function_name
}

output "scheduler_function_arn" {
  value = aws_lambda_function.scheduler.arn
}

output "rightsizing_function_name" {
  value = aws_lambda_function.rightsizing.function_name
}

output "rightsizing_function_arn" {
  value = aws_lambda_function.rightsizing.arn
}

output "sns_topic_arn" {
  value = aws_sns_topic.notifications.arn
}