locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  }
}

module "storage" {
  source = "./modules/storage"

  environment  = var.environment
  project_name = var.project_name
  tags         = local.common_tags
}

module "cdn" {
  source = "./modules/cdn"

  environment        = var.environment
  project_name       = var.project_name
  origin_domain_name = module.storage.bucket_regional_domain_name
  origin_bucket_arn  = module.storage.bucket_arn
  tags               = local.common_tags
}

# Bucket policy is defined at root level to break the circular dependency
# between storage (needs CloudFront ARN) and CDN (needs bucket domain name).
resource "aws_s3_bucket_policy" "webui_cloudfront" {
  bucket = module.storage.bucket_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${module.storage.bucket_arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = module.cdn.distribution_arn
          }
        }
      }
    ]
  })
}

module "compute" {
  source = "./modules/compute"

  environment             = var.environment
  project_name            = var.project_name
  runtime                 = "python3.12"
  memory_size             = var.lambda_memory_size
  timeout                 = var.lambda_timeout
  handler                 = "handler.handler"
  deployment_package_path = var.deployment_package_path
  environment_variables = merge(var.app_environment_variables, {
    DYNAMODB_TABLE_NAME = module.compute.cases_table_name
  })
  tags                    = local.common_tags
}

module "networking" {
  source = "./modules/networking"

  environment          = var.environment
  project_name         = var.project_name
  lambda_invoke_arn    = module.compute.invoke_arn
  lambda_function_name = module.compute.function_name
  cors_allowed_origins = var.cors_allowed_origins
  tags                 = local.common_tags
}
