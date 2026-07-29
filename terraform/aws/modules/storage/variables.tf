variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
}

variable "project_name" {
  type        = string
  description = "Project name used in resource naming"
}

variable "tags" {
  type        = map(string)
  description = "Common resource tags"
  default     = {}
}
