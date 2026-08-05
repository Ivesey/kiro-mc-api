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

variable "database_name" {
  type        = string
  description = "Cosmos DB database name"
  default     = "microdigitech-cases"
}

variable "container_name" {
  type        = string
  description = "Cosmos DB container name"
  default     = "cases"
}

variable "partition_key_path" {
  type        = string
  description = "Partition key path for the container"
  default     = "/case_id"
}

variable "consistency_level" {
  type        = string
  description = "Cosmos DB consistency level"
  default     = "Session"
}

variable "capacity_mode" {
  type        = string
  description = "Cosmos DB capacity mode (Serverless or Provisioned)"
  default     = "Serverless"
}

variable "tags" {
  type        = map(string)
  description = "Resource tags to apply"
  default     = {}
}
