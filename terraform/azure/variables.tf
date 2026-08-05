variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "azure_region" {
  type        = string
  description = "Azure region for resource deployment"
  default     = "eastus"
}

variable "project_name" {
  type        = string
  description = "Project name used in resource naming and tagging"
  default     = "microdigitech-cases"
}

variable "cors_allowed_origins" {
  type        = list(string)
  description = "List of origins allowed for CORS on the Function App"
  default     = ["*"]
}

variable "deployment_package_path" {
  type        = string
  description = "Path to the Azure Functions deployment ZIP archive"
  default     = "../../dist/azure_functions.zip"
}

variable "app_environment_variables" {
  type        = map(string)
  description = "Environment variables passed to the Function App for Pydantic BaseSettings"
  default     = {}
}

variable "cosmosdb_consistency_level" {
  type        = string
  description = "Cosmos DB consistency level"
  default     = "Session"
  validation {
    condition     = contains(["Strong", "BoundedStaleness", "Session", "ConsistentPrefix", "Eventual"], var.cosmosdb_consistency_level)
    error_message = "Consistency level must be one of: Strong, BoundedStaleness, Session, ConsistentPrefix, Eventual."
  }
}

variable "cosmosdb_capacity_mode" {
  type        = string
  description = "Cosmos DB capacity mode (Serverless or Provisioned)"
  default     = "Serverless"
  validation {
    condition     = contains(["Serverless", "Provisioned"], var.cosmosdb_capacity_mode)
    error_message = "Capacity mode must be one of: Serverless, Provisioned."
  }
}
