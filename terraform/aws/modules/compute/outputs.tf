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

output "cases_table_name" {
  value       = aws_dynamodb_table.cases.name
  description = "DynamoDB cases table name"
}

output "cases_table_arn" {
  value       = aws_dynamodb_table.cases.arn
  description = "DynamoDB cases table ARN"
}
