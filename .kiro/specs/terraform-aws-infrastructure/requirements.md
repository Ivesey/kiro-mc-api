# Requirements Document

## Introduction

This specification defines the Terraform infrastructure-as-code requirements for deploying the MicroDigitech Support Cases application to AWS using a serverless architecture. The WebUI (static HTML/CSS/JS) is hosted as an S3 static website served through CloudFront, and the API layer (FastAPI) runs on AWS Lambda behind API Gateway. The Terraform directory structure is organized to accommodate future multi-cloud deployments (GCP, Azure).

## Glossary

- **Terraform_Module**: A reusable, self-contained collection of Terraform configuration files that manages a specific piece of infrastructure
- **Static_Website_Bucket**: An S3 bucket configured for static website hosting that serves the WebUI assets (HTML, CSS, JS, images)
- **Lambda_Function**: An AWS Lambda function that runs the FastAPI application using the Mangum adapter for ASGI-to-Lambda translation
- **API_Gateway**: An AWS API Gateway HTTP API that routes incoming HTTP requests to the Lambda_Function
- **CloudFront_Distribution**: An AWS CloudFront CDN distribution that serves the Static_Website_Bucket content with HTTPS and caching
- **IAM_Execution_Role**: An AWS IAM role assumed by the Lambda_Function during execution, granting access to required AWS services
- **Terraform_State_Backend**: The remote storage configuration for Terraform state files, enabling team collaboration and state locking
- **Deployment_Pipeline**: The set of Terraform configurations and variable files that enable environment-specific deployments (dev, staging, production)
- **Provider_Directory**: A top-level directory within the terraform folder dedicated to a single cloud provider (e.g., aws, gcp, azure)

## Requirements

### Requirement 1: Multi-Cloud Directory Structure

**User Story:** As a DevOps engineer, I want the Terraform configuration organized by cloud provider, so that I can add GCP and Azure deployments in the future without restructuring existing code.

#### Acceptance Criteria

1. THE Terraform_Module SHALL be organized under a `terraform/` directory at the project root with a separate Provider_Directory for each cloud provider
2. THE Provider_Directory for AWS SHALL be located at `terraform/aws/` and contain all AWS-specific Terraform configurations including at minimum a root module entry point file and a variables definition file
3. THE Terraform_Module SHALL use a modular structure where each logical infrastructure component (networking, compute, storage, CDN) resides in its own subdirectory within the Provider_Directory, each containing its own Terraform configuration files independent of other component subdirectories
4. WHEN a new cloud provider is added, THE Terraform_Module SHALL allow creation of a new Provider_Directory without modifying any files within existing Provider_Directories, ensuring no cross-provider resource references or shared mutable state exist between Provider_Directories
5. THE Provider_Directory SHALL contain no direct references to resources defined in another Provider_Directory, so that each provider's configuration can be planned and applied in isolation

### Requirement 2: Static Website Hosting

**User Story:** As a DevOps engineer, I want the WebUI deployed as a static S3 website behind CloudFront, so that the frontend is served globally with low latency and HTTPS.

#### Acceptance Criteria

1. THE Static_Website_Bucket SHALL store all WebUI assets (index.html, styles.css, JavaScript files, image files, and favicon files)
2. THE Static_Website_Bucket SHALL block all direct public access and allow access only through the CloudFront_Distribution using an Origin Access Control policy
3. THE CloudFront_Distribution SHALL serve the Static_Website_Bucket content over HTTPS with TLS 1.2 or higher
4. THE CloudFront_Distribution SHALL use `index.html` as the default root object
5. IF a request is made to a path that does not match a stored object, THEN THE CloudFront_Distribution SHALL return `index.html` with an HTTP 200 status code to support client-side routing
6. THE CloudFront_Distribution SHALL cache static assets (JavaScript files, CSS files, image files, and favicon files) with a default TTL of 86400 seconds (24 hours) and SHALL cache `index.html` with a maximum TTL of 300 seconds (5 minutes) to allow deployment propagation
7. WHEN a request is made over plain HTTP, THE CloudFront_Distribution SHALL redirect the request to the equivalent HTTPS URL

### Requirement 3: Lambda Function Deployment

**User Story:** As a DevOps engineer, I want the FastAPI application deployed to AWS Lambda, so that the API runs serverlessly with automatic scaling and no server management.

#### Acceptance Criteria

1. THE Lambda_Function SHALL execute the FastAPI application using the Mangum ASGI adapter as the Lambda handler, with the handler entry point defined as a module-level callable that wraps the FastAPI app instance
2. THE Lambda_Function SHALL use the Python 3.12 runtime
3. THE Lambda_Function SHALL be configured with a memory allocation of 256 MB and a timeout of 30 seconds
4. THE Lambda_Function SHALL include all application dependencies from `api/requirements.txt` in the deployment package
5. THE Lambda_Function SHALL be deployed from a ZIP archive containing the application code and dependencies, not exceeding the Lambda deployment package size limits (50 MB zipped, 250 MB unzipped)
6. THE IAM_Execution_Role SHALL grant the Lambda_Function permission to write logs to CloudWatch Logs
7. THE Lambda_Function SHALL be accessible via an HTTP integration (API Gateway HTTP API) that routes incoming HTTP requests to the Lambda handler
8. THE Lambda_Function SHALL be configured with environment variables required by the application's configuration layer so that Pydantic BaseSettings can resolve all required settings at runtime
9. IF the Lambda_Function fails to initialize or encounters an unhandled runtime error, THEN THE Lambda_Function SHALL return an error response indicating the failure and log the error details to CloudWatch Logs

### Requirement 4: API Gateway Configuration

**User Story:** As a DevOps engineer, I want an API Gateway exposing the Lambda function as HTTP endpoints, so that the API is accessible over the internet with a stable URL.

#### Acceptance Criteria

1. THE API_Gateway SHALL be an HTTP API (APIGatewayV2) that routes all HTTP methods and paths to the Lambda_Function using an AWS_PROXY integration type
2. THE API_Gateway SHALL use a catch-all route (`$default`) that proxies all requests to the Lambda_Function with auto-deploy enabled on the default stage (`$default` stage)
3. THE API_Gateway SHALL enable CORS with allowed origins configurable via Terraform variable, allowed methods set to all HTTP methods used by the API (GET, POST, PUT, PATCH, DELETE, OPTIONS), allowed headers including Content-Type and Authorization, and a max age of 7200 seconds
4. THE API_Gateway SHALL output the invoke URL as a Terraform output value for use by the WebUI configuration
5. WHEN the API_Gateway is deployed, THE Terraform_Module SHALL output the base API URL including the stage path as a Terraform output named distinctly from the raw invoke URL, so that the WebUI can use it directly without path manipulation

### Requirement 5: IAM and Security

**User Story:** As a DevOps engineer, I want the infrastructure to follow least-privilege security principles, so that each component has only the permissions it requires.

#### Acceptance Criteria

1. THE IAM_Execution_Role SHALL grant only the permissions for the Lambda_Function to invoke the Lambda runtime (`lambda:InvokeFunction`) and write CloudWatch logs (`logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`), with no additional service permissions attached
2. THE Static_Website_Bucket SHALL have a bucket policy that denies all access except requests originating from the CloudFront_Distribution via an Origin Access Control (OAC) condition, and SHALL have public access block enabled on all four settings (BlockPublicAcls, IgnorePublicAcls, BlockPublicPolicy, RestrictPublicBuckets)
3. THE Lambda_Function SHALL have a resource-based permission policy that allows invocation only by the API_Gateway service principal (`apigateway.amazonaws.com`) scoped to the specific API Gateway resource ARN
4. THE Terraform_Module SHALL not hard-code any AWS credentials, secret keys, or access tokens in any `.tf` configuration files or variable default values
5. THE Terraform_Module SHALL use Terraform variables marked as `sensitive = true` for all secret or credential values, and SHALL use variables (without sensitive marking) for all environment-specific configuration values such as region, account ID, and domain names
6. IF the IAM_Execution_Role requires access to additional AWS services beyond CloudWatch Logs, THEN THE Terraform_Module SHALL define each additional permission as a separate IAM policy statement scoped to the minimum required resource ARN rather than using wildcard (`*`) resource references
7. IF a Terraform variable defined as `sensitive = true` is referenced in an output, THEN THE Terraform_Module SHALL mark that output as `sensitive = true` to prevent the value from appearing in CLI output or state file summaries

### Requirement 6: Terraform State Management

**User Story:** As a DevOps engineer, I want Terraform state managed remotely, so that team members can collaborate and state is not lost.

#### Acceptance Criteria

1. THE Terraform_State_Backend SHALL accept configuration variables for S3 bucket name, bucket region, DynamoDB table name, and state file key to define the remote state storage and locking target
2. THE Terraform_State_Backend SHALL be defined in a separate backend configuration file, with each environment specifying its own state file key to prevent cross-environment state collisions
3. IF no remote backend configuration is provided, THEN THE Terraform_Module SHALL initialize using a local state file in the working directory without requiring network access
4. IF the DynamoDB state lock cannot be acquired within 60 seconds, THEN THE Terraform_State_Backend SHALL fail the operation and return an error message indicating the lock is held by another process

### Requirement 7: Environment Configuration

**User Story:** As a DevOps engineer, I want to deploy to multiple environments (dev, staging, production) using the same Terraform code, so that I can promote changes safely through environments.

#### Acceptance Criteria

1. THE Terraform_Module SHALL accept a variable for environment name restricted to a predefined set of allowed values (dev, staging, prod) with a maximum length of 10 alphanumeric lowercase characters, and SHALL use this value as a prefix in all created resource names and identifiers to ensure uniqueness per environment
2. THE Terraform_Module SHALL use `.tfvars` files to define environment-specific values for each deployment target
3. THE Terraform_Module SHALL tag all AWS resources with an "Environment" tag set to the environment name, a "Project" tag set to the project name, and a "ManagedBy" tag set to a value indicating Terraform
4. WHEN the environment variable changes, THE Terraform_Module SHALL produce resources with unique names prefixed by the environment value and use a separate state file per environment, so that no resource name or state conflicts occur between environment deployments
5. IF the environment variable is set to a value outside the predefined allowed set, THEN THE Terraform_Module SHALL fail validation with an error message indicating the invalid environment name and the list of allowed values

### Requirement 8: Terraform Outputs and WebUI Integration

**User Story:** As a DevOps engineer, I want Terraform to output the deployed API URL, so that the WebUI can be configured to call the correct API endpoint after deployment.

#### Acceptance Criteria

1. WHEN a Terraform apply completes successfully, THE Terraform_Module SHALL output the API_Gateway invoke URL as a complete URL including the protocol scheme (e.g., `https://<id>.execute-api.<region>.amazonaws.com`)
2. WHEN a Terraform apply completes successfully, THE Terraform_Module SHALL output the CloudFront_Distribution domain name as a complete HTTPS URL (e.g., `https://<distribution>.cloudfront.net`)
3. THE Terraform_Module SHALL output the Static_Website_Bucket name as a named output value that deployment scripts can reference to sync WebUI assets
4. THE Terraform_Module SHALL output the API_Gateway invoke URL under an output name that the WebUI configuration can reference to set the API base endpoint at deployment time
5. THE Terraform_Module SHALL mark all output values containing URLs or resource identifiers with a `description` attribute indicating the output's intended consumer (WebUI configuration or deployment script)
