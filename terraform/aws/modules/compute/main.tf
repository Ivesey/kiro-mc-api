locals {
  function_name = "${var.environment}-${var.project_name}-api"
  role_name     = "${var.environment}-${var.project_name}-lambda-role"
}

# IAM Role for Lambda execution
resource "aws_iam_role" "lambda_execution" {
  name = local.role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM Role Policy - CloudWatch Logs permissions only (least privilege)
resource "aws_iam_role_policy" "lambda_logging" {
  name = "${local.role_name}-logging"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.lambda.arn}:*"
      }
    ]
  })
}

# CloudWatch Log Group for the Lambda function
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = 14

  tags = var.tags
}

# Lambda Function
resource "aws_lambda_function" "api" {
  function_name    = local.function_name
  role             = aws_iam_role.lambda_execution.arn
  handler          = var.handler
  runtime          = var.runtime
  memory_size      = var.memory_size
  timeout          = var.timeout
  filename         = var.deployment_package_path
  source_code_hash = filebase64sha256(var.deployment_package_path)

  environment {
    variables = var.environment_variables
  }

  depends_on = [
    aws_iam_role_policy.lambda_logging,
    aws_cloudwatch_log_group.lambda
  ]

  tags = var.tags
}
