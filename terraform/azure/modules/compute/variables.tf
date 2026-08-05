variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
}

variable "project_name" {
  type        = string
  description = "Project name used in resource naming"
}

variable "resource_group_name" {
  type        = string
  description = "Name of the resource group to deploy into"
}

variable "azure_region" {
  type        = string
  description = "Azure region for resource deployment"
}

variable "deployment_package_path" {
  type        = string
  description = "Path to the Azure Functions deployment ZIP archive"
}

variable "app_settings" {
  type        = map(string)
  description = "Application settings (environment variables) for the Function App"
  default     = {}
}

variable "cors_allowed_origins" {
  type        = list(string)
  description = "List of origins allowed for CORS on the Function App"
  default     = ["*"]
}

variable "tags" {
  type        = map(string)
  description = "Common resource tags"
  default     = {}
}
