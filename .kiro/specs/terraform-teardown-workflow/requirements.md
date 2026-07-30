# Requirements Document

## Introduction

A GitHub Actions workflow that tears down AWS infrastructure provisioned by Terraform. The workflow is triggered manually via `workflow_dispatch` and defaults to destroying all three environments (dev, staging, prod), with an option to target a single environment. It mirrors the existing deploy workflow's authentication, backend configuration, and secrets.

## Glossary

- **Teardown_Workflow**: The GitHub Actions workflow defined in `.github/workflows/teardown-aws.yml` that executes `terraform destroy` to remove AWS infrastructure.
- **Environment**: One of the three deployment targets: dev, staging, or prod. Each has its own Terraform state file and tfvars configuration.
- **OIDC_Authentication**: OpenID Connect-based authentication that allows GitHub Actions to assume an AWS IAM role without long-lived credentials.
- **Backend_Config**: The Terraform remote state configuration using an S3 bucket and DynamoDB table for state locking.
- **Var_File**: An environment-specific `.tfvars` file located at `terraform/aws/environments/{env}.tfvars` that provides Terraform variable values.

## Requirements

### Requirement 1: Manual Trigger with Environment Selection

**User Story:** As a DevOps engineer, I want to manually trigger the teardown workflow with an option to select which environments to destroy, so that I can control infrastructure removal precisely.

#### Acceptance Criteria

1. THE Teardown_Workflow SHALL be triggered exclusively via workflow_dispatch.
2. THE Teardown_Workflow SHALL provide an environment input of type choice with options: "all", "dev", "staging", "prod".
3. THE Teardown_Workflow SHALL default the environment input to "all".
4. WHEN the environment input is "all", THE Teardown_Workflow SHALL execute terraform destroy for dev, staging, and prod environments in sequence, processing dev first, then staging, then prod.
5. WHEN the environment input is a single environment name, THE Teardown_Workflow SHALL execute terraform destroy for that environment only.
6. IF terraform destroy fails for an environment during sequential execution, THEN THE Teardown_Workflow SHALL halt execution and not proceed to subsequent environments, and SHALL report the failure.

### Requirement 2: OIDC Authentication

**User Story:** As a DevOps engineer, I want the teardown workflow to authenticate using the same OIDC mechanism as the deploy workflow, so that credentials are managed consistently and securely.

#### Acceptance Criteria

1. THE Teardown_Workflow SHALL request `id-token: write` and `contents: read` permissions at the workflow level.
2. THE Teardown_Workflow SHALL authenticate to AWS via OIDC by using the `aws-actions/configure-aws-credentials@v4` action with the `role-to-assume` parameter set to the `AWS_ROLE_ARN` secret.
3. THE Teardown_Workflow SHALL pass the `AWS_REGION` variable to the `aws-region` parameter of the credentials action, falling back to "us-east-1" when the variable is not set.
4. IF the OIDC authentication step fails, THEN THE Teardown_Workflow SHALL terminate without executing any subsequent steps.

### Requirement 3: Terraform Backend Configuration

**User Story:** As a DevOps engineer, I want the teardown workflow to initialise Terraform with the correct remote backend for each environment, so that it targets the correct state file during destroy.

#### Acceptance Criteria

1. THE Teardown_Workflow SHALL run `terraform init` with backend-config parameters for bucket, dynamodb_table, region, and key from the `terraform/aws` working directory.
2. THE Teardown_Workflow SHALL use the `TF_STATE_BUCKET` secret for the bucket backend-config.
3. THE Teardown_Workflow SHALL use the `TF_STATE_DYNAMODB_TABLE` secret for the dynamodb_table backend-config.
4. THE Teardown_Workflow SHALL use key format `{environment}/terraform.tfstate` where environment is one of "dev", "staging", or "prod" as selected by the workflow input.
5. THE Teardown_Workflow SHALL use the `AWS_REGION` variable with fallback to "us-east-1" for the region backend-config.
6. THE Teardown_Workflow SHALL use identical backend-config parameter values as the deploy workflow for the same environment, ensuring the init targets the same remote state file that was written during provisioning.

### Requirement 4: Terraform Destroy Execution

**User Story:** As a DevOps engineer, I want the workflow to execute `terraform destroy` with the correct var-file for each target environment, so that all provisioned resources are removed.

#### Acceptance Criteria

1. WHEN a teardown is triggered for a target environment, THE Teardown_Workflow SHALL execute `terraform destroy -auto-approve` with `-var-file="environments/{env}.tfvars"` where `{env}` is the selected environment name (one of: dev, staging, prod).
2. THE Teardown_Workflow SHALL pass `-var="environment={env}"` to the destroy command, matching the variable assignment used during the original `terraform apply`.
3. THE Teardown_Workflow SHALL set the working directory to `terraform/aws` for all Terraform commands.
4. THE Teardown_Workflow SHALL initialize Terraform with the same backend configuration used during provisioning before executing the destroy command.
5. IF the `terraform destroy` command exits with a non-zero status code, THEN THE Teardown_Workflow SHALL fail the workflow run and report the error without proceeding to subsequent environments.

### Requirement 5: Multi-Environment Teardown Order

**User Story:** As a DevOps engineer, I want the teardown of all environments to proceed in a safe order, so that dependencies between environments are respected.

#### Acceptance Criteria

1. WHEN the environment input is "all", THE Teardown_Workflow SHALL destroy environments sequentially in the order: dev, staging, prod, where each environment's teardown must complete successfully before the next environment's teardown begins.
2. IF terraform destroy returns a non-zero exit code for an environment, THEN THE Teardown_Workflow SHALL skip all subsequent environments, fail the workflow, and include the name of the failed environment in the workflow run summary.
3. WHEN the environment input is "all", THE Teardown_Workflow SHALL execute terraform destroy with the corresponding environment-specific var-file and state key for each environment in the sequence.

### Requirement 6: Workflow File Location

**User Story:** As a DevOps engineer, I want the teardown workflow to be placed at the conventional path alongside the deploy workflow, so that it is discoverable and consistent.

#### Acceptance Criteria

1. THE Teardown_Workflow SHALL be defined in the file `.github/workflows/teardown-aws.yml`.
2. THE Teardown_Workflow SHALL have its `name` field set to "Teardown AWS Infrastructure".
3. THE Teardown_Workflow file SHALL reside in the same directory as the existing `deploy-aws.yml` workflow.
