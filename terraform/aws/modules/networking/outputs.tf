output "api_invoke_url" {
  value       = aws_apigatewayv2_stage.default.invoke_url
  description = "API Gateway invoke URL for WebUI configuration to set API base endpoint"
}

output "api_id" {
  value       = aws_apigatewayv2_api.this.id
  description = "API Gateway HTTP API ID"
}
