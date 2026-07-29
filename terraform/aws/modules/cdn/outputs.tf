output "distribution_domain_name" {
  value       = aws_cloudfront_distribution.this.domain_name
  description = "CloudFront distribution domain name"
}

output "distribution_arn" {
  value       = aws_cloudfront_distribution.this.arn
  description = "CloudFront distribution ARN for S3 bucket policy"
}

output "distribution_id" {
  value       = aws_cloudfront_distribution.this.id
  description = "CloudFront distribution ID for cache invalidation"
}
