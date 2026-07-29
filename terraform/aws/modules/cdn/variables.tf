variable "environment" {
  type        = string
  description = "Deployment environment (dev, staging, prod)"
}

variable "project_name" {
  type        = string
  description = "Project name used in resource naming"
}

variable "origin_domain_name" {
  type        = string
  description = "S3 bucket regional domain name used as CloudFront origin"
}

variable "origin_bucket_arn" {
  type        = string
  description = "S3 bucket ARN for OAC policy reference"
}

variable "default_ttl" {
  type        = number
  description = "Default cache TTL in seconds for static assets"
  default     = 86400
}

variable "index_max_ttl" {
  type        = number
  description = "Maximum TTL in seconds for index.html caching"
  default     = 300
}

variable "tags" {
  type        = map(string)
  description = "Common resource tags"
  default     = {}
}
