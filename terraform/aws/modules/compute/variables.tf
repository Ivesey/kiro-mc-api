variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
}

variable "project_name" {
  type        = string
  description = "Project name used in resource naming and tagging"
}

variable "runtime" {
  type        = string
  description = "Lambda runtime identifier (e.g., python3.12)"
}

variable "memory_size" {
  type        = number
  description = "Lambda function memory allocation in MB"
}

variable "timeout" {
  type        = number
  description = "Lambda function timeout in seconds"
}

variable "handler" {
  type        = string
  description = "Lambda handler entry point (e.g., handler.handler)"
}

variable "deployment_package_path" {
  type        = string
  description = "Path to the Lambda deployment ZIP archive"
}

variable "environment_variables" {
  type        = map(string)
  description = "Environment variables passed to the Lambda function for Pydantic BaseSettings"
  default     = {}
}

variable "tags" {
  type        = map(string)
  description = "Common resource tags applied to all resources"
  default     = {}
}
