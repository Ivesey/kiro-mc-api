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

variable "tags" {
  type        = map(string)
  description = "Common resource tags"
}
