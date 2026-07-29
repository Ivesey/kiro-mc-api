# Implementation Plan: Terraform AWS Infrastructure

## Overview

This plan implements the Terraform infrastructure for deploying the MicroDigitech Support Cases application to AWS. The implementation follows a modular approach: first creating the directory structure and shared configuration, then building each module (storage, CDN, compute, networking), composing them in the root module, and finally adding environment-specific variable files and outputs.

## Tasks

- [x] 1. Set up Terraform directory structure and provider configuration
  - [x] 1.1 Create the directory structure and provider configuration
    - Create `terraform/aws/` directory with `providers.tf` configuring the AWS provider with region from variable
    - Create `terraform/aws/main.tf` as the root module entry point (empty initially, will compose modules later)
    - Create placeholder directories: `terraform/aws/modules/storage/`, `terraform/aws/modules/cdn/`, `terraform/aws/modules/compute/`, `terraform/aws/modules/networking/`, `terraform/aws/environments/`
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 1.2 Create root-level variables and backend configuration
    - Create `terraform/aws/variables.tf` with all root variables: `environment` (with validation for dev/staging/prod), `aws_region`, `project_name`, `lambda_memory_size`, `lambda_timeout`, `cors_allowed_origins`, `deployment_package_path`, `app_environment_variables`
    - Create `terraform/aws/backend.tf` with S3 backend configuration using partial configuration pattern (bucket, region, dynamodb_table, key as backend config args)
    - Create `terraform/aws/terraform.tfvars` with non-sensitive defaults
    - _Requirements: 1.2, 5.4, 5.5, 6.1, 6.2, 6.3, 7.1, 7.5_

- [x] 2. Implement the storage module (S3 static website bucket)
  - [x] 2.1 Create the storage module configuration
    - Create `terraform/aws/modules/storage/variables.tf` with inputs: `environment`, `project_name`, `cloudfront_distribution_arn`, `tags`
    - Create `terraform/aws/modules/storage/main.tf` with:
      - `aws_s3_bucket` resource named `{environment}-{project_name}-webui`
      - `aws_s3_bucket_public_access_block` with all four block settings enabled (BlockPublicAcls, IgnorePublicAcls, BlockPublicPolicy, RestrictPublicBuckets)
      - `aws_s3_bucket_policy` allowing access only from CloudFront via OAC condition
    - Create `terraform/aws/modules/storage/outputs.tf` exposing `bucket_name`, `bucket_arn`, `bucket_regional_domain_name`
    - _Requirements: 2.1, 2.2, 5.2_

- [x] 3. Implement the CDN module (CloudFront distribution)
  - [x] 3.1 Create the CDN module configuration
    - Create `terraform/aws/modules/cdn/variables.tf` with inputs: `environment`, `project_name`, `origin_domain_name`, `origin_bucket_arn`, `default_ttl`, `index_max_ttl`, `tags`
    - Create `terraform/aws/modules/cdn/main.tf` with:
      - `aws_cloudfront_origin_access_control` resource for S3 origin
      - `aws_cloudfront_distribution` resource with:
        - S3 origin using OAC
        - Default root object set to `index.html`
        - Viewer protocol policy set to `redirect-to-https`
        - Default cache behavior with TTL of 86400s for static assets
        - Ordered cache behavior for `index.html` with max TTL of 300s
        - Custom error response returning `index.html` with 200 for 403/404 errors (SPA routing)
        - TLS minimum protocol version TLSv1.2
    - Create `terraform/aws/modules/cdn/outputs.tf` exposing `distribution_domain_name`, `distribution_arn`, `distribution_id`
    - _Requirements: 2.3, 2.4, 2.5, 2.6, 2.7_

- [x] 4. Implement the compute module (Lambda function + IAM)
  - [x] 4.1 Create the compute module configuration
    - Create `terraform/aws/modules/compute/variables.tf` with inputs: `environment`, `project_name`, `runtime`, `memory_size`, `timeout`, `handler`, `deployment_package_path`, `environment_variables`, `tags`
    - Create `terraform/aws/modules/compute/main.tf` with:
      - `aws_iam_role` for Lambda execution with assume role policy for `lambda.amazonaws.com`
      - `aws_iam_role_policy` granting CloudWatch Logs permissions only (`logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`)
      - `aws_lambda_function` resource configured with Python 3.12 runtime, 256MB memory, 30s timeout, ZIP deployment package, environment variables map, and handler pointing to Mangum-wrapped FastAPI app
      - `aws_cloudwatch_log_group` for the Lambda function with retention policy
    - Create `terraform/aws/modules/compute/outputs.tf` exposing `function_arn`, `function_name`, `invoke_arn`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.8, 3.9, 5.1_

- [x] 5. Implement the networking module (API Gateway)
  - [x] 5.1 Create the networking module configuration
    - Create `terraform/aws/modules/networking/variables.tf` with inputs: `environment`, `project_name`, `lambda_invoke_arn`, `lambda_function_name`, `cors_allowed_origins`, `tags`
    - Create `terraform/aws/modules/networking/main.tf` with:
      - `aws_apigatewayv2_api` HTTP API resource with CORS configuration (allowed origins from variable, methods: GET/POST/PUT/PATCH/DELETE/OPTIONS, headers: Content-Type/Authorization, max_age: 7200)
      - `aws_apigatewayv2_integration` with AWS_PROXY integration to Lambda
      - `aws_apigatewayv2_route` with `$default` catch-all route
      - `aws_apigatewayv2_stage` with `$default` stage and auto-deploy enabled
      - `aws_lambda_permission` granting API Gateway invocation scoped to specific API Gateway ARN
    - Create `terraform/aws/modules/networking/outputs.tf` exposing `api_invoke_url`, `api_id`
    - _Requirements: 3.7, 4.1, 4.2, 4.3, 4.4, 4.5, 5.3_

- [x] 6. Checkpoint - Validate module structure
  - Ensure all modules have valid Terraform syntax by running `terraform fmt -check -recursive terraform/aws/` and `terraform validate`. Ask the user if questions arise.

- [x] 7. Compose modules in root main.tf and create outputs
  - [x] 7.1 Wire all modules together in the root main.tf
    - Update `terraform/aws/main.tf` to:
      - Define `locals` block with common tags (Environment, Project, ManagedBy)
      - Instantiate `module "storage"` passing environment, project_name, cloudfront_distribution_arn (from cdn module), tags
      - Instantiate `module "cdn"` passing origin_domain_name and origin_bucket_arn from storage module, TTL values, tags
      - Instantiate `module "compute"` passing runtime, memory, timeout, handler (`handler.handler`), deployment_package_path, environment_variables, tags
      - Instantiate `module "networking"` passing lambda_invoke_arn and lambda_function_name from compute module, cors_allowed_origins, tags
      - Handle circular dependency between storage and cdn using a two-pass approach or `depends_on`
    - _Requirements: 1.3, 7.3_

  - [x] 7.2 Create root-level outputs
    - Create `terraform/aws/outputs.tf` with described outputs:
      - `api_invoke_url` — API Gateway invoke URL (description: "for WebUI configuration")
      - `cloudfront_url` — Full HTTPS CloudFront URL (description: "for WebUI access")
      - `website_bucket_name` — S3 bucket name (description: "for deployment scripts to sync WebUI assets")
      - `cloudfront_distribution_id` — Distribution ID (description: "for deployment scripts to invalidate cache")
    - All outputs include `description` attribute indicating intended consumer
    - _Requirements: 4.4, 4.5, 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 8. Create environment-specific variable files
  - [x] 8.1 Create tfvars files for each environment
    - Create `terraform/aws/environments/dev.tfvars` with dev-specific values (environment="dev", smaller resources if applicable, permissive CORS for development)
    - Create `terraform/aws/environments/staging.tfvars` with staging-specific values (environment="staging")
    - Create `terraform/aws/environments/prod.tfvars` with production-specific values (environment="prod", restrictive CORS)
    - Each environment uses a distinct state key in backend configuration
    - _Requirements: 7.1, 7.2, 7.4_

- [x] 9. Create Lambda deployment packaging script
  - [x] 9.1 Create a deployment package build script
    - Create `scripts/build_lambda_package.py` (or shell script) that:
      - Creates a temporary build directory
      - Installs dependencies from `api/requirements.txt` into the build directory
      - Copies the `api/app/` source code into the build directory
      - Creates a `handler.py` at the package root that imports the FastAPI app and wraps it with Mangum as the Lambda handler entry point
      - Zips the build directory into `dist/lambda.zip`
      - Validates the ZIP is under 50MB
    - Add `mangum` to `api/requirements.txt` as a dependency for Lambda deployment
    - _Requirements: 3.1, 3.4, 3.5_

- [x] 10. Final checkpoint - Full validation
  - Run `terraform fmt -check -recursive terraform/aws/` to verify formatting
  - Run `terraform -chdir=terraform/aws init -backend=false` to initialize without remote backend
  - Run `terraform -chdir=terraform/aws validate` to verify configuration validity
  - Run `terraform -chdir=terraform/aws plan -var-file=environments/dev.tfvars` to verify plan succeeds (requires AWS credentials)
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- This feature is Infrastructure as Code (Terraform/HCL), so property-based testing does not apply. Validation is done through `terraform validate`, `terraform plan`, and formatting checks.
- Each task references specific requirements for traceability.
- Checkpoints ensure incremental validation of the Terraform configuration.
- The storage and CDN modules have a circular dependency (bucket policy needs CloudFront ARN, CloudFront needs bucket domain). This is resolved by passing the CloudFront distribution ARN to the storage module and using `depends_on` or splitting the bucket policy into a separate resource.
- The Lambda deployment package script (task 9) is a prerequisite for running `terraform plan` with the compute module, since it references the ZIP file path.
- Environment-specific deployments use: `terraform plan -var-file=environments/<env>.tfvars`
- Remote state initialization uses: `terraform init -backend-config=<backend-config-file>`

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["2.1", "4.1", "5.1"] },
    { "id": 3, "tasks": ["3.1"] },
    { "id": 4, "tasks": ["7.1", "8.1"] },
    { "id": 5, "tasks": ["7.2"] },
    { "id": 6, "tasks": ["9.1"] }
  ]
}
```
