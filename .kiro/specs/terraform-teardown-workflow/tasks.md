# Implementation Plan: Terraform Teardown Workflow

## Overview

Create a GitHub Actions workflow file at `.github/workflows/teardown-aws.yml` that safely tears down AWS infrastructure provisioned by Terraform. The workflow supports destroying a single environment or all three (dev, staging, prod) in sequence with fail-fast behavior. It reuses the same OIDC authentication, backend configuration, and secrets as the existing deploy workflow.

## Tasks

- [x] 1. Create the teardown workflow file
  - [x] 1.1 Create `.github/workflows/teardown-aws.yml` with workflow_dispatch trigger and environment input
    - Set workflow `name` to "Teardown AWS Infrastructure"
    - Add `workflow_dispatch` trigger with `environment` choice input (options: all, dev, staging, prod; default: "all")
    - Set workflow-level permissions: `id-token: write`, `contents: read`
    - Define single job `teardown` running on `ubuntu-latest`
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 6.1, 6.2, 6.3_

  - [x] 1.2 Add checkout and AWS OIDC authentication steps
    - Add `actions/checkout@v4` step
    - Add `aws-actions/configure-aws-credentials@v4` step with `role-to-assume: ${{ secrets.AWS_ROLE_ARN }}` and `aws-region: ${{ vars.AWS_REGION || 'us-east-1' }}`
    - Match the exact action versions and parameter structure from the deploy workflow
    - _Requirements: 2.2, 2.3, 2.4_

  - [x] 1.3 Add Terraform setup and destroy loop step
    - Add `hashicorp/setup-terraform@v3` step
    - Add a shell step that determines the environment list based on input (all environments or single)
    - Use `set -e` for fail-fast behavior
    - Loop over target environments in order: dev, staging, prod
    - For each environment, run `terraform init` with backend-config for bucket (`TF_STATE_BUCKET`), dynamodb_table (`TF_STATE_DYNAMODB_TABLE`), region (`AWS_REGION` with us-east-1 fallback), and key (`{env}/terraform.tfstate`)
    - For each environment, run `terraform destroy -auto-approve -var="environment={env}" -var-file="environments/{env}.tfvars"`
    - Set `working-directory: terraform/aws` for all Terraform commands
    - On failure, write the failed environment name to `$GITHUB_STEP_SUMMARY`
    - _Requirements: 1.4, 1.5, 1.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3_

- [x] 2. Final checkpoint
  - Verify the workflow file is valid YAML, review against the deploy workflow for consistency in secrets/variables usage, and ask the user if questions arise.

## Notes

- This feature produces a single YAML file — no application code or tests are needed
- Property-based testing does not apply (IaC/declarative YAML, no application logic)
- The workflow reuses all secrets and variables from the existing deploy workflow
- The destroy loop uses `set -e` to guarantee fail-fast; no subsequent environments are processed after a failure
- Backend-config values must exactly mirror the deploy workflow to target the correct state files

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3"] }
  ]
}
```
