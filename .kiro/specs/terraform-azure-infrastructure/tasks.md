# Implementation Plan: Terraform Azure Infrastructure

## Overview

This plan implements the Azure infrastructure-as-code deployment for the MicroDigitech Support Cases application. It creates the Terraform configuration at `terraform/azure/`, parallel to `terraform/aws/`, along with the CosmosDB data access layer, Azure Functions build script, GitHub Actions workflows, and associated tests. Each task builds incrementally, wiring components together as they are created.

## Tasks

- [x] 1. Scaffold Terraform directory structure and root module files
  - [x] 1.1 Create root module files (`providers.tf`, `backend.tf`, `variables.tf`, `main.tf`, `outputs.tf`, `terraform.tfvars`)
    - Create `terraform/azure/providers.tf` with `azurerm` provider configuration (features block)
    - Create `terraform/azure/backend.tf` with partial `azurerm` backend configuration (resource_group_name, storage_account_name, container_name, key)
    - Create `terraform/azure/variables.tf` with all root-level variables: `environment` (with validation), `azure_region`, `project_name`, `cors_allowed_origins`, `deployment_package_path`, `app_environment_variables`, `cosmosdb_consistency_level` (with validation), `cosmosdb_capacity_mode` (with validation)
    - Create `terraform/azure/main.tf` with `locals` block for `common_tags` and resource group creation (`azurerm_resource_group`)
    - Create `terraform/azure/outputs.tf` with placeholder outputs (will be populated as modules are added)
    - Create `terraform/azure/terraform.tfvars` with sensible non-sensitive defaults
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 1.2 Create environment tfvars files
    - Create `terraform/azure/environments/dev.tfvars` with dev-specific values
    - Create `terraform/azure/environments/staging.tfvars` with staging-specific values
    - Create `terraform/azure/environments/prod.tfvars` with prod-specific values
    - Each file sets `environment` to its respective value and any environment-specific overrides
    - _Requirements: 1.4, 2.4, 3.3_

- [x] 2. Implement Storage module (Blob Storage with static website)
  - [x] 2.1 Create storage module files
    - Create `terraform/azure/modules/storage/main.tf` with `azurerm_storage_account` (static website enabled, index_document = "index.html") and `locals` for naming (alphanumeric, max 24 chars pattern `{env}{short}web`)
    - Create `terraform/azure/modules/storage/variables.tf` with inputs: `environment`, `project_name`, `resource_group_name`, `azure_region`, `tags`
    - Create `terraform/azure/modules/storage/outputs.tf` with outputs: `storage_account_name`, `primary_web_endpoint`, `primary_web_host`
    - _Requirements: 1.3, 4.1, 4.2, 4.3, 7.4_

  - [x] 2.2 Wire storage module into root main.tf
    - Add `module "storage"` block to `terraform/azure/main.tf` passing required variables
    - Update `terraform/azure/outputs.tf` with `storage_account_name` output
    - _Requirements: 8.3_

- [x] 3. Implement CDN module (Azure CDN profile and endpoint)
  - [x] 3.1 Create CDN module files
    - Create `terraform/azure/modules/cdn/main.tf` with `azurerm_cdn_profile` (Standard_Microsoft SKU), `azurerm_cdn_endpoint` (origin pointing to storage static website host, HTTPS redirect delivery rule, caching configuration)
    - Create `terraform/azure/modules/cdn/variables.tf` with inputs: `environment`, `project_name`, `resource_group_name`, `azure_region`, `origin_host_name`, `tags`
    - Create `terraform/azure/modules/cdn/outputs.tf` with outputs: `cdn_endpoint_hostname`, `cdn_profile_name`, `cdn_endpoint_name`
    - _Requirements: 1.3, 4.4, 4.5, 4.6, 4.7_

  - [x] 3.2 Wire CDN module into root main.tf
    - Add `module "cdn"` block to `terraform/azure/main.tf` passing `origin_host_name` from storage module output
    - Update `terraform/azure/outputs.tf` with `cdn_url`, `cdn_profile_name`, `cdn_endpoint_name` outputs with descriptions
    - _Requirements: 8.2, 8.4, 8.5_

- [x] 4. Implement Database module (Cosmos DB)
  - [x] 4.1 Create database module files
    - Create `terraform/azure/modules/database/main.tf` with `azurerm_cosmosdb_account` (NoSQL/SQL API, configurable consistency level, serverless by default), `azurerm_cosmosdb_sql_database`, `azurerm_cosmosdb_sql_container` (partition key `/case_id`)
    - Create `terraform/azure/modules/database/variables.tf` with inputs: `environment`, `project_name`, `resource_group_name`, `azure_region`, `database_name`, `container_name`, `partition_key_path`, `consistency_level`, `capacity_mode`, `tags`
    - Create `terraform/azure/modules/database/outputs.tf` with outputs: `cosmosdb_endpoint`, `cosmosdb_primary_key` (sensitive), `cosmosdb_database_name`, `cosmosdb_container_name`
    - _Requirements: 1.3, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9, 12.11_

  - [x] 4.2 Wire database module into root main.tf
    - Add `module "database"` block to `terraform/azure/main.tf` passing variables from root
    - Update `terraform/azure/outputs.tf` with `cosmosdb_endpoint` output
    - _Requirements: 12.10, 8.1_

- [x] 5. Implement Compute module (Function App)
  - [x] 5.1 Create compute module files
    - Create `terraform/azure/modules/compute/main.tf` with `azurerm_service_plan` (Linux, Consumption SKU Y1), dedicated `azurerm_storage_account` for Functions runtime, `azurerm_linux_function_app` (Python 3.12, system-assigned identity, ZIP deploy, app_settings from variable including Cosmos DB connection settings)
    - Create `terraform/azure/modules/compute/variables.tf` with inputs: `environment`, `project_name`, `resource_group_name`, `azure_region`, `deployment_package_path`, `app_settings`, `tags`
    - Create `terraform/azure/modules/compute/outputs.tf` with outputs: `function_app_name`, `function_app_default_hostname`, `identity_principal_id`, `function_app_id`
    - _Requirements: 1.3, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 6.1, 7.1_

  - [x] 5.2 Wire compute module into root main.tf
    - Add `module "compute"` block to `terraform/azure/main.tf` passing Cosmos DB outputs as app_settings (COSMOSDB_ENDPOINT, COSMOSDB_KEY, COSMOSDB_DATABASE_NAME, COSMOSDB_CONTAINER_NAME, DAL_IMPLEMENTATION)
    - Update `terraform/azure/outputs.tf` with `function_app_url` output
    - _Requirements: 8.1, 12.10_

- [x] 6. Implement Networking module (CORS)
  - [x] 6.1 Create networking module files
    - Create `terraform/azure/modules/networking/main.tf` that configures CORS on the Function App (allowed origins, allowed methods GET/POST/PUT/PATCH/DELETE/OPTIONS)
    - Create `terraform/azure/modules/networking/variables.tf` with inputs: `function_app_id`, `cors_allowed_origins`
    - Create `terraform/azure/modules/networking/outputs.tf` with output: `function_app_url`
    - _Requirements: 1.3, 6.2, 6.3, 6.4, 6.5_

  - [x] 6.2 Wire networking module into root main.tf
    - Add `module "networking"` block to `terraform/azure/main.tf` passing `function_app_id` from compute module and `cors_allowed_origins` from root variable
    - _Requirements: 6.2, 6.3_

- [x] 7. Checkpoint - Validate Terraform configuration
  - Ensure all Terraform files are syntactically valid by running `terraform fmt -check -recursive terraform/azure/` and `terraform -chdir=terraform/azure init -backend=false && terraform -chdir=terraform/azure validate`
  - Verify no references to `terraform/aws/` resources exist
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement CosmosDB Data Access Layer
  - [x] 8.1 Create `api/azure_dal/` module with CosmosDB DAL implementation
    - Create `api/azure_dal/__init__.py` exporting `CosmosDBCaseDAL`
    - Create `api/azure_dal/cosmosdb_case_dal.py` implementing all `CaseDAL` abstract methods (`create_case`, `update_case`, `delete_case`, `get_all_cases`, `get_case_by_id`)
    - Use `azure-cosmos` SDK, read config from Pydantic BaseSettings (`cosmosdb_endpoint`, `cosmosdb_key`, `cosmosdb_database_name`, `cosmosdb_container_name`)
    - Map `CosmosResourceExistsError` → `ValueError` in `create_case`
    - Map `CosmosResourceNotFoundError` → `KeyError` in `update_case`, `delete_case`, `get_case_by_id`
    - Use `case_id` as both partition key and `id` field
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9_

  - [x] 8.2 Extend `api/app/config.py` with CosmosDB settings
    - Add `cosmosdb_endpoint: str = ""`, `cosmosdb_key: str = ""`, `cosmosdb_database_name: str = "microdigitech-cases"`, `cosmosdb_container_name: str = "cases"` to `AppSettings`
    - _Requirements: 11.10, 11.4_

  - [x] 8.3 Create `api/requirements-azure.txt` with Azure SDK dependencies
    - Include `azure-functions`, `azure-cosmos`, and other Azure-specific pinned dependencies
    - Keep separate from AWS dependencies in `api/requirements-aws.txt`
    - _Requirements: 10.2_

  - [x] 8.4 Write unit tests for CosmosDB DAL
    - Create `api/tests/dal/test_cosmosdb_case_dal.py` with mock-based tests using `unittest.mock.patch` on `azure.cosmos` SDK
    - Test `create_case` with duplicate raises `ValueError`
    - Test `get_case_by_id` not found raises `KeyError`
    - Test `update_case` not found raises `KeyError`
    - Test `delete_case` not found raises `KeyError`
    - Test `get_all_cases` returns deserialized list
    - Test serialization/deserialization preserves all fields
    - Test initialization fails without endpoint/key settings
    - _Requirements: 11.2, 11.6, 11.7, 11.8_

- [x] 9. Implement Azure Functions build script
  - [x] 9.1 Create `scripts/build_azure_functions_package.py`
    - Mirror structure of `scripts/build_lambda_package.py`
    - Validate prerequisites (`api/requirements-azure.txt`, `api/app/` exist) with descriptive error messages
    - Install dependencies from `api/requirements-azure.txt` into build directory
    - Copy `api/app/` source code into build directory
    - Generate `function_app.py` entry point (Azure Functions ASGI adapter wrapping FastAPI app)
    - Generate `host.json` (version 2.0, extension bundle)
    - Create ZIP archive at `dist/azure_functions.zip`
    - Validate ZIP size (warn at 500MB, fail at 1GB)
    - Clean up build directory
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_

  - [x] 9.2 Write unit tests for build script
    - Create `tests/test_build_azure_functions_package.py` at project root
    - Test exit code 1 when `requirements-azure.txt` is missing
    - Test exit code 1 when `api/app/` directory is missing
    - Test ZIP contains `function_app.py` and `host.json`
    - Test ZIP contains `app/` directory with source code
    - Test generated `function_app.py` content matches expected template
    - Test generated `host.json` content matches expected schema
    - _Requirements: 10.4, 10.5, 10.8_

- [x] 10. Checkpoint - Verify DAL and build script
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Create GitHub Actions deploy workflow
  - [x] 11.1 Create `.github/workflows/deploy-azure.yml`
    - Trigger: `workflow_dispatch` with environment choice (dev, staging, prod)
    - Permissions: `id-token: write`, `contents: read`
    - Steps: checkout, setup Python 3.12, Azure Login via OIDC (`azure/login@v2`), build Azure Functions package, setup Terraform, `terraform init` with backend-config, `terraform plan`, `terraform apply`, deploy WebUI via `az storage blob upload-batch`, purge CDN cache via `az cdn endpoint purge`, print Function App URL and CDN URL
    - Use secrets: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `AZURE_TF_STATE_RESOURCE_GROUP`, `AZURE_TF_STATE_STORAGE_ACCOUNT`, `AZURE_TF_STATE_CONTAINER`
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9_

- [x] 12. Create GitHub Actions teardown workflow
  - [x] 12.1 Create `.github/workflows/teardown-azure.yml`
    - Trigger: `workflow_dispatch` with environment choice (all, dev, staging, prod)
    - Permissions: `id-token: write`, `contents: read`
    - Steps: checkout, Azure Login via OIDC, setup Terraform, create placeholder ZIP, loop through target environments running `terraform init -reconfigure` and `terraform destroy -auto-approve`
    - Write success/failure messages to GitHub Step Summary
    - Use same secrets as deploy workflow
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9, 13.10, 13.11_

- [x] 13. Final checkpoint - End-to-end validation
  - Run `terraform fmt -check -recursive terraform/azure/`
  - Run `terraform -chdir=terraform/azure init -backend=false && terraform -chdir=terraform/azure validate`
  - Run all Python unit tests: `venv\Scripts\pytest api/tests/dal/test_cosmosdb_case_dal.py`
  - Verify no hard-coded credentials in any `.tf` files
  - Verify all sensitive outputs are marked `sensitive = true`
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation via Terraform fmt/validate and pytest
- The design document does not include a Correctness Properties section (IaC/declarative configuration), so property-based tests are not applicable
- Unit tests use `unittest.mock.patch` to mock the `azure.cosmos` SDK, consistent with existing DynamoDB DAL test patterns
- The existing `terraform/aws/` and `scripts/build_lambda_package.py` serve as structural references for the Azure equivalents

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1", "4.1", "8.1", "8.2", "8.3"] },
    { "id": 2, "tasks": ["2.2", "3.1", "4.2", "5.1", "9.1"] },
    { "id": 3, "tasks": ["3.2", "5.2", "8.4", "9.2"] },
    { "id": 4, "tasks": ["6.1"] },
    { "id": 5, "tasks": ["6.2", "11.1", "12.1"] }
  ]
}
```
