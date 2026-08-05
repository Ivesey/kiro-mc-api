# Requirements Document

## Introduction

This specification defines the Terraform infrastructure-as-code requirements for deploying the MicroDigitech Support Cases application to Microsoft Azure, mirroring the existing AWS deployment architecture. The WebUI (static HTML/CSS/JS) is hosted on Azure Blob Storage with static website hosting, served globally via Azure CDN. The API layer (FastAPI) runs on Azure Functions (Python, Consumption Plan) with HTTP triggers. A GitHub Actions workflow (`deploy-azure.yml`) automates deployment using OIDC-based authentication. The Terraform directory structure is placed at `terraform/azure/`, parallel to the existing `terraform/aws/`.

## Glossary

- **Terraform_Module**: A reusable, self-contained collection of Terraform configuration files that manages a specific piece of Azure infrastructure
- **Azure_Resource_Group**: An Azure resource group that contains all deployed resources for a given environment, providing a logical boundary for management and billing
- **Static_Website_Storage**: An Azure Storage Account with static website hosting enabled that serves the WebUI assets (HTML, CSS, JS, images)
- **Azure_CDN_Profile**: An Azure CDN profile and endpoint that caches and serves the Static_Website_Storage content globally with HTTPS
- **Function_App**: An Azure Functions application (Python, Consumption Plan) that runs the FastAPI application using an Azure Functions HTTP trigger adapter
- **App_Service_Plan**: An Azure App Service Plan (Consumption tier) that hosts the Function_App with automatic scaling and pay-per-execution billing
- **Managed_Identity**: A system-assigned managed identity attached to the Function_App, used for authentication to other Azure services without stored credentials
- **Terraform_State_Backend**: An Azure Storage Account with a blob container used for Terraform remote state storage with blob lease-based state locking
- **Deployment_Pipeline**: The GitHub Actions workflow (`deploy-azure.yml`) that builds, provisions, and deploys the application to Azure using OIDC authentication
- **Service_Principal**: An Azure Active Directory application registration with federated OIDC credentials, used by the Deployment_Pipeline for authentication without stored secrets
- **Provider_Directory**: The `terraform/azure/` directory containing all Azure-specific Terraform configurations, parallel to `terraform/aws/`
- **CosmosDB_DAL**: A Python module at `api/azure_dal/` implementing the CaseDAL abstract interface using the Azure Cosmos DB NoSQL (SQL API) SDK for data persistence
- **CosmosDB_Account**: An Azure Cosmos DB account provisioned via Terraform for storing application data with the NoSQL (SQL) API
- **CosmosDB_Database**: A logical database within the CosmosDB_Account that contains one or more containers
- **CosmosDB_Container**: A container within the CosmosDB_Database that stores JSON items, partitioned by `case_id`
- **Database_Module**: The Terraform child module at `terraform/azure/modules/database/` that provisions the CosmosDB_Account, CosmosDB_Database, and CosmosDB_Container
- **Teardown_Workflow**: The GitHub Actions workflow (`teardown-azure.yml`) that destroys Azure infrastructure provisioned by Terraform, supporting single-environment or full teardown

## Requirements

### Requirement 1: Azure Provider Directory Structure

**User Story:** As a DevOps engineer, I want the Azure Terraform configuration organized in a parallel directory to the existing AWS configuration, so that both cloud deployments coexist without interference.

#### Acceptance Criteria

1. THE Terraform_Module SHALL be located at `terraform/azure/` within the project root, parallel to the existing `terraform/aws/` directory
2. THE Provider_Directory for Azure SHALL contain a root module entry point file (`main.tf`), a variables definition file (`variables.tf`), an outputs file (`outputs.tf`), a providers file (`providers.tf`), and a backend configuration file (`backend.tf`)
3. THE Terraform_Module SHALL use a modular structure with child modules located at `terraform/azure/modules/storage/`, `terraform/azure/modules/cdn/`, `terraform/azure/modules/compute/`, `terraform/azure/modules/networking/`, and `terraform/azure/modules/database/`, each containing its own `main.tf`, `variables.tf`, and `outputs.tf`
4. THE Provider_Directory SHALL contain an `environments/` subdirectory with `.tfvars` files for dev, staging, and prod environments
5. THE Provider_Directory SHALL contain no references to resources defined in `terraform/aws/`, so that Azure infrastructure can be planned and applied independently of AWS

### Requirement 2: Azure Terraform State Management

**User Story:** As a DevOps engineer, I want Terraform state for Azure stored remotely in Azure Blob Storage, so that team members can collaborate and state is protected with locking.

#### Acceptance Criteria

1. THE Terraform_State_Backend SHALL use the `azurerm` backend type with configuration for resource group name, storage account name, container name, and state file key
2. THE Terraform_State_Backend SHALL be defined with partial configuration, accepting backend parameters via `-backend-config` flags during `terraform init`
3. WHEN multiple operators run Terraform concurrently, THE Terraform_State_Backend SHALL use Azure Blob Storage lease-based locking to prevent concurrent state modifications
4. THE Terraform_Module SHALL use a separate state file key per environment (e.g., `dev/terraform.tfstate`, `staging/terraform.tfstate`, `prod/terraform.tfstate`) to prevent cross-environment state collisions
5. IF no remote backend configuration is provided, THEN THE Terraform_Module SHALL initialize using a local state file in the working directory without requiring network access

### Requirement 3: Azure Resource Group and Common Configuration

**User Story:** As a DevOps engineer, I want all Azure resources grouped in a resource group with consistent naming and tagging, so that resources are organized and discoverable per environment.

#### Acceptance Criteria

1. THE Terraform_Module SHALL create one Azure_Resource_Group per deployment that contains all resources for that environment
2. THE Terraform_Module SHALL name the Azure_Resource_Group using the pattern `{environment}-{project_name}-rg` (e.g., `dev-microdigitech-cases-rg`)
3. THE Terraform_Module SHALL accept a variable for environment name restricted to the allowed values `dev`, `staging`, and `prod`, and SHALL use this value as a prefix in all created resource names
4. THE Terraform_Module SHALL tag all Azure resources with an `Environment` tag set to the environment name, a `Project` tag set to the project name, and a `ManagedBy` tag set to `terraform`
5. THE Terraform_Module SHALL accept an `azure_region` variable (defaulting to `eastus`) specifying the Azure region for all resource deployment
6. IF the environment variable is set to a value outside the predefined allowed set, THEN THE Terraform_Module SHALL fail validation with an error message indicating the invalid environment name and the list of allowed values

### Requirement 4: Static Website Hosting on Azure Blob Storage

**User Story:** As a DevOps engineer, I want the WebUI deployed as a static website on Azure Blob Storage behind Azure CDN, so that the frontend is served globally with low latency and HTTPS.

#### Acceptance Criteria

1. THE Static_Website_Storage SHALL be an Azure Storage Account with static website hosting enabled, serving `index.html` as the index document
2. THE Static_Website_Storage SHALL store all WebUI assets (index.html, styles.css, JavaScript files, image files, and favicon files) in the `$web` blob container
3. THE Static_Website_Storage SHALL be named using the pattern `{environment}{project_short}web` (alphanumeric, lowercase, max 24 characters) to comply with Azure Storage Account naming restrictions
4. THE Azure_CDN_Profile SHALL serve the Static_Website_Storage content over HTTPS with TLS 1.2 or higher
5. THE Azure_CDN_Profile SHALL use the static website primary endpoint of the Static_Website_Storage as the origin
6. THE Azure_CDN_Profile SHALL cache static assets (JavaScript files, CSS files, image files) with a default TTL and SHALL support cache purging for deployment updates
7. WHEN a request is made over plain HTTP, THE Azure_CDN_Profile SHALL redirect the request to the equivalent HTTPS URL

### Requirement 5: Azure Functions Compute

**User Story:** As a DevOps engineer, I want the FastAPI application deployed to Azure Functions, so that the API runs serverlessly with automatic scaling equivalent to the AWS Lambda deployment.

#### Acceptance Criteria

1. THE Function_App SHALL execute the FastAPI application using an Azure Functions HTTP trigger adapter (azure-functions adapter wrapping the ASGI app), with the function entry point callable defined in a function app module
2. THE Function_App SHALL use the Python 3.12 runtime on a Linux Consumption Plan (App_Service_Plan)
3. THE Function_App SHALL be configured with application settings (environment variables) required by the application's configuration layer so that Pydantic BaseSettings can resolve all required settings at runtime
4. THE Function_App SHALL be deployed from a ZIP package containing the application code, dependencies, and Azure Functions host configuration files (`host.json`, `function_app.py`)
5. THE Function_App SHALL have a system-assigned Managed_Identity enabled for authenticating to other Azure services
6. THE Terraform_Module SHALL create a dedicated Azure Storage Account for the Function_App runtime (required by the Azure Functions platform for trigger management and logging)
7. THE Function_App SHALL be named using the pattern `{environment}-{project_name}-func` to maintain naming consistency
8. IF the Function_App fails to initialize or encounters an unhandled runtime error, THEN THE Function_App SHALL return an HTTP error response and log the error details to Azure Application Insights or the Functions log stream

### Requirement 6: API Networking and CORS

**User Story:** As a DevOps engineer, I want the Azure Function exposed as HTTP endpoints with CORS configured, so that the WebUI can call the API from the browser.

#### Acceptance Criteria

1. THE Function_App SHALL expose HTTP trigger endpoints accessible over HTTPS via the Azure Functions default hostname (`https://{function-app-name}.azurewebsites.net`)
2. THE Function_App SHALL enable CORS with allowed origins configurable via Terraform variable, matching the pattern used in the AWS API Gateway CORS configuration
3. THE Terraform_Module SHALL output the Function_App default hostname as a complete HTTPS URL for use by the WebUI configuration
4. THE Function_App SHALL accept all HTTP methods used by the API (GET, POST, PUT, PATCH, DELETE, OPTIONS) on its HTTP trigger
5. WHEN the CORS allowed origins variable is set to `["*"]`, THE Function_App SHALL allow requests from all origins

### Requirement 7: IAM and Security

**User Story:** As a DevOps engineer, I want the Azure infrastructure to follow least-privilege security principles, so that each component has only the permissions it requires.

#### Acceptance Criteria

1. THE Function_App SHALL use a system-assigned Managed_Identity for authenticating to Azure services, with no connection strings or service keys stored in application settings for Azure service access
2. THE Terraform_Module SHALL not hard-code any Azure credentials, client secrets, tenant IDs, or subscription IDs in any `.tf` configuration files or variable default values
3. THE Terraform_Module SHALL use Terraform variables marked as `sensitive = true` for all secret or credential values
4. THE Static_Website_Storage SHALL restrict write access to the deployment pipeline only, with public read access limited to the `$web` container via the static website endpoint
5. THE Terraform_Module SHALL define IAM role assignments scoped to the minimum required resource (specific storage account, specific resource group) rather than using subscription-level wildcard permissions
6. IF a Terraform variable defined as `sensitive = true` is referenced in an output, THEN THE Terraform_Module SHALL mark that output as `sensitive = true` to prevent the value from appearing in CLI output

### Requirement 8: Terraform Outputs and WebUI Integration

**User Story:** As a DevOps engineer, I want Terraform to output the deployed API URL, CDN URL, and storage account details, so that deployment scripts and the WebUI can reference the correct endpoints.

#### Acceptance Criteria

1. WHEN a Terraform apply completes successfully, THE Terraform_Module SHALL output the Function_App default hostname as a complete HTTPS URL (e.g., `https://{name}.azurewebsites.net`)
2. WHEN a Terraform apply completes successfully, THE Terraform_Module SHALL output the Azure_CDN_Profile endpoint hostname as a complete HTTPS URL (e.g., `https://{endpoint}.azureedge.net`)
3. THE Terraform_Module SHALL output the Static_Website_Storage account name as a named output value that deployment scripts can reference to upload WebUI assets
4. THE Terraform_Module SHALL output the Azure_CDN_Profile endpoint name and profile name as named output values that deployment scripts can reference to purge the CDN cache
5. THE Terraform_Module SHALL mark all output values with a `description` attribute indicating the output's intended consumer (WebUI configuration, deployment script, or CDN purge)

### Requirement 9: GitHub Actions Deployment Workflow for Azure

**User Story:** As a DevOps engineer, I want a GitHub Actions workflow that deploys the application to Azure using OIDC, so that deployments are automated and credential-free, mirroring the AWS workflow structure.

#### Acceptance Criteria

1. THE Deployment_Pipeline SHALL be defined in `.github/workflows/deploy-azure.yml` and triggered manually via `workflow_dispatch` with an environment input (choice of dev, staging, prod)
2. THE Deployment_Pipeline SHALL authenticate to Azure using OIDC federated credentials via the `azure/login` GitHub Action, requiring no stored client secrets
3. THE Deployment_Pipeline SHALL require the GitHub secrets `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and `AZURE_SUBSCRIPTION_ID` for OIDC authentication, and `AZURE_TF_STATE_RESOURCE_GROUP`, `AZURE_TF_STATE_STORAGE_ACCOUNT`, and `AZURE_TF_STATE_CONTAINER` for Terraform backend configuration
4. THE Deployment_Pipeline SHALL build the Azure Functions deployment package using a Python build script (parallel to `scripts/build_lambda_package.py`) that installs dependencies, copies application code, creates the Azure Functions adapter entry point, and produces a ZIP archive
5. THE Deployment_Pipeline SHALL run `terraform init`, `terraform plan`, and `terraform apply` with the appropriate environment `.tfvars` file and backend configuration
6. THE Deployment_Pipeline SHALL deploy WebUI assets to the Static_Website_Storage `$web` container using the Azure CLI (`az storage blob upload-batch`)
7. THE Deployment_Pipeline SHALL purge the Azure_CDN_Profile endpoint cache after deploying WebUI assets
8. WHEN the workflow completes successfully, THE Deployment_Pipeline SHALL print the Function_App URL and the Azure CDN URL as workflow outputs
9. THE Deployment_Pipeline SHALL request `id-token: write` and `contents: read` permissions to enable OIDC token generation

### Requirement 10: Azure Functions Build Script

**User Story:** As a DevOps engineer, I want a build script that produces an Azure Functions deployment package, so that the same FastAPI application can be packaged for Azure without modifying the application code.

#### Acceptance Criteria

1. THE build script SHALL be located at `scripts/build_azure_functions_package.py`, parallel to the existing `scripts/build_lambda_package.py`
2. THE build script SHALL install dependencies from `api/requirements-azure.txt` into a build directory
3. THE build script SHALL copy the `api/app/` source code into the build directory
4. THE build script SHALL create an Azure Functions entry point file (`function_app.py`) that wraps the FastAPI application using the `azure.functions` ASGI adapter
5. THE build script SHALL create a `host.json` configuration file with Azure Functions runtime settings (version 2, Python worker)
6. THE build script SHALL produce a ZIP archive at `dist/azure_functions.zip` containing all application code, dependencies, and Azure Functions configuration files
7. THE build script SHALL validate that the produced ZIP archive does not exceed Azure Functions deployment package size limits
8. IF the `api/requirements-azure.txt` file or `api/app/` directory does not exist, THEN THE build script SHALL exit with a non-zero status code and a descriptive error message

### Requirement 11: CosmosDB Data Access Layer

**User Story:** As a developer, I want a CosmosDB implementation of the CaseDAL interface, so that the application can persist support cases in Azure Cosmos DB as an alternative to AWS DynamoDB.

#### Acceptance Criteria

1. THE CosmosDB_DAL SHALL be located at `api/azure_dal/cosmosdb_case_dal.py`, parallel to the existing `api/aws_dal/dynamodb_case_dal.py`
2. THE CosmosDB_DAL SHALL implement all abstract methods defined in the `CaseDAL` interface (`create_case`, `update_case`, `delete_case`, `get_all_cases`, `get_case_by_id`)
3. THE CosmosDB_DAL SHALL use the `azure-cosmos` SDK (CosmosDB NoSQL/SQL API) for all data operations
4. THE CosmosDB_DAL SHALL read connection configuration from Pydantic BaseSettings, accepting `cosmosdb_endpoint`, `cosmosdb_key`, `cosmosdb_database_name`, and `cosmosdb_container_name` as settings
5. THE CosmosDB_DAL SHALL use `case_id` as both the partition key value and the item `id` field when storing items in the CosmosDB_Container
6. WHEN `create_case` is called with a `case_id` that already exists in the CosmosDB_Container, THE CosmosDB_DAL SHALL raise a `ValueError` with a message indicating the duplicate case_id
7. WHEN `update_case`, `delete_case`, or `get_case_by_id` is called with a `case_id` that does not exist in the CosmosDB_Container, THE CosmosDB_DAL SHALL raise a `KeyError` with the case_id value
8. THE CosmosDB_DAL SHALL serialize CaseModel instances to JSON-compatible dictionaries and deserialize CosmosDB items back to CaseModel instances
9. THE `api/azure_dal/__init__.py` module SHALL export the `CosmosDBCaseDAL` class so that importing from `azure_dal` provides access to the implementation
10. THE application configuration in `api/app/config.py` SHALL accept `cosmosdb_endpoint`, `cosmosdb_key`, `cosmosdb_database_name`, and `cosmosdb_container_name` as optional settings so that the CosmosDB_DAL can be selected via the `dal_implementation` setting
11. WHEN the `dal_implementation` setting is set to `CosmosDBCaseDAL`, THE application SHALL instantiate the CosmosDB_DAL for handling all case data operations

### Requirement 12: CosmosDB Terraform Module

**User Story:** As a DevOps engineer, I want a Terraform module that provisions an Azure Cosmos DB account, database, and container, so that the CosmosDB_DAL has a properly configured data store in each environment.

#### Acceptance Criteria

1. THE Database_Module SHALL be located at `terraform/azure/modules/database/` containing `main.tf`, `variables.tf`, and `outputs.tf`
2. THE Database_Module SHALL provision a CosmosDB_Account using the NoSQL (SQL) API with consistency level configurable via a Terraform variable (defaulting to `Session` consistency)
3. THE Database_Module SHALL provision a CosmosDB_Database within the CosmosDB_Account with a name configurable via a Terraform variable
4. THE Database_Module SHALL provision a CosmosDB_Container within the CosmosDB_Database with a partition key path set to `/case_id`
5. THE Database_Module SHALL configure throughput for the CosmosDB_Container using serverless capacity mode or provisioned throughput (configurable via variable, defaulting to serverless) to align with the consumption-based billing model of the rest of the infrastructure
6. THE Database_Module SHALL name the CosmosDB_Account using the pattern `{environment}-{project_name}-cosmos` to maintain naming consistency with other resources
7. THE Database_Module SHALL accept a `resource_group_name` and `azure_region` variable to deploy into the correct Azure_Resource_Group and region
8. THE Database_Module SHALL output the CosmosDB_Account endpoint URL, primary key, database name, and container name for use by the Function_App application settings
9. THE Database_Module SHALL mark the primary key output as `sensitive = true` to prevent it from appearing in CLI output
10. THE Terraform_Module root module SHALL invoke the Database_Module and pass its outputs to the Function_App application settings so that the CosmosDB_DAL can connect at runtime
11. THE Database_Module SHALL apply the standard resource tags (`Environment`, `Project`, `ManagedBy`) consistent with all other provisioned resources

### Requirement 13: Azure Teardown GitHub Workflow

**User Story:** As a DevOps engineer, I want a GitHub Actions workflow that destroys Azure infrastructure via Terraform, so that environments can be cleanly deprovisioned when no longer needed, mirroring the existing AWS teardown workflow.

#### Acceptance Criteria

1. THE Teardown_Workflow SHALL be defined in `.github/workflows/teardown-azure.yml` and triggered manually via `workflow_dispatch` with an environment input (choice of all, dev, staging, prod)
2. THE Teardown_Workflow SHALL authenticate to Azure using OIDC federated credentials via the `azure/login` GitHub Action, requiring the GitHub secrets `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and `AZURE_SUBSCRIPTION_ID`
3. THE Teardown_Workflow SHALL use the GitHub secrets `AZURE_TF_STATE_RESOURCE_GROUP`, `AZURE_TF_STATE_STORAGE_ACCOUNT`, and `AZURE_TF_STATE_CONTAINER` for Terraform backend configuration during initialization
4. THE Teardown_Workflow SHALL create a placeholder Azure Functions ZIP package in the `dist/` directory before running Terraform, so that Terraform variable validation for the deployment package path succeeds
5. WHEN the environment input is set to `all`, THE Teardown_Workflow SHALL destroy dev, staging, and prod environments in sequence
6. WHEN the environment input is set to a single environment (dev, staging, or prod), THE Teardown_Workflow SHALL destroy only that environment
7. THE Teardown_Workflow SHALL run `terraform init -reconfigure` with Azure backend configuration parameters (resource group, storage account, container name, and environment-specific state key) before each environment destroy operation
8. THE Teardown_Workflow SHALL run `terraform destroy -auto-approve` with the corresponding environment `.tfvars` file for each targeted environment
9. WHEN a `terraform destroy` operation fails for an environment, THE Teardown_Workflow SHALL write a failure message to the GitHub Step Summary and exit with a non-zero status code
10. WHEN all targeted environments are destroyed successfully, THE Teardown_Workflow SHALL write a success message to the GitHub Step Summary
11. THE Teardown_Workflow SHALL request `id-token: write` and `contents: read` permissions to enable OIDC token generation

