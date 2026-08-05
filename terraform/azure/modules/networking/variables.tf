variable "function_app_id" {
  type        = string
  description = "Function App resource ID to look up for URL output"
}

variable "cors_allowed_origins" {
  type        = list(string)
  description = "List of origins allowed for CORS on the Function App"
  default     = ["*"]
}
