variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
}

variable "project_name" {
  type        = string
  description = "Project name used in resource naming"
}

variable "lambda_invoke_arn" {
  type        = string
  description = "Lambda function invoke ARN for API Gateway integration"
}

variable "lambda_function_name" {
  type        = string
  description = "Lambda function name for resource-based permission policy"
}

variable "cors_allowed_origins" {
  type        = list(string)
  description = "List of origins allowed for CORS on the API Gateway"
}

variable "tags" {
  type        = map(string)
  description = "Common resource tags applied to all resources"
  default     = {}
}
