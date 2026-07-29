variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "aws_region" {
  type        = string
  description = "AWS region for resource deployment"
  default     = "us-east-1"
}

variable "project_name" {
  type        = string
  description = "Project name used in resource naming and tagging"
  default     = "microdigitech-cases"
}

variable "lambda_memory_size" {
  type        = number
  description = "Lambda function memory allocation in MB"
  default     = 256
}

variable "lambda_timeout" {
  type        = number
  description = "Lambda function timeout in seconds"
  default     = 30
}

variable "cors_allowed_origins" {
  type        = list(string)
  description = "List of origins allowed for CORS on the API Gateway"
  default     = ["*"]
}

variable "deployment_package_path" {
  type        = string
  description = "Path to the Lambda deployment ZIP archive"
  default     = "../../dist/lambda.zip"
}

variable "app_environment_variables" {
  type        = map(string)
  description = "Environment variables passed to the Lambda function for Pydantic BaseSettings"
  default     = {}
}
