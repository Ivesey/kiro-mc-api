output "bucket_name" {
  value       = aws_s3_bucket.webui.id
  description = "S3 bucket name for deployment scripts to sync WebUI assets"
}

output "bucket_arn" {
  value       = aws_s3_bucket.webui.arn
  description = "S3 bucket ARN for IAM policies and CloudFront OAC"
}

output "bucket_regional_domain_name" {
  value       = aws_s3_bucket.webui.bucket_regional_domain_name
  description = "S3 bucket regional domain name for CloudFront origin configuration"
}
