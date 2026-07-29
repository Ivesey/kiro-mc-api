output "api_invoke_url" {
  value       = module.networking.api_invoke_url
  description = "API Gateway invoke URL for WebUI configuration to set API base endpoint"
}

output "cloudfront_url" {
  value       = "https://${module.cdn.distribution_domain_name}"
  description = "CloudFront distribution HTTPS URL for WebUI access"
}

output "website_bucket_name" {
  value       = module.storage.bucket_name
  description = "S3 bucket name for deployment scripts to sync WebUI assets"
}

output "cloudfront_distribution_id" {
  value       = module.cdn.distribution_id
  description = "CloudFront distribution ID for deployment scripts to invalidate cache"
}
