output "function_arn" {
  value       = aws_lambda_function.api.arn
  description = "Lambda function ARN"
}

output "function_name" {
  value       = aws_lambda_function.api.function_name
  description = "Lambda function name"
}

output "invoke_arn" {
  value       = aws_lambda_function.api.invoke_arn
  description = "Lambda invoke ARN for API Gateway integration"
}
