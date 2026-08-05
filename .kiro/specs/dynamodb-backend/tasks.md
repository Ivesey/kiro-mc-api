# Implementation Plan: DynamoDB Backend

## Overview

This plan implements DynamoDB as a persistent backend for the support cases API across three layers: Terraform infrastructure (table + IAM), Python application (DynamoDBCaseDAL), and modularity (importlib-based dynamic resolution via `DAL_IMPLEMENTATION` env var). Each task builds incrementally — infrastructure first, then application code, then wiring and integration.

## Tasks

- [x] 1. Terraform: DynamoDB table and IAM policy in compute module
  - [x] 1.1 Add DynamoDB table resource and IAM policy to the compute module
    - Add `aws_dynamodb_table.cases` resource to `terraform/aws/modules/compute/main.tf` with partition key `case_id` (String), PAY_PER_REQUEST billing, name pattern `{environment}-{project_name}-cases`, and common tags
    - Add `aws_iam_role_policy.lambda_dynamodb` resource granting `dynamodb:*` on the table ARN and `table/*/index/*`
    - Add `depends_on` for `aws_iam_role_policy.lambda_dynamodb` to the Lambda function resource
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.4_

  - [x] 1.2 Add compute module outputs and root module wiring
    - Add `cases_table_name` and `cases_table_arn` outputs to `terraform/aws/modules/compute/outputs.tf`
    - Update `terraform/aws/main.tf` to pass `DYNAMODB_TABLE_NAME = module.compute.cases_table_name` and `DAL_IMPLEMENTATION = "aws_dal.dynamodb_case_dal.DynamoDBCaseDAL"` in the environment variables map (use `merge` with `var.app_environment_variables`)
    - _Requirements: 1.5, 1.6, 2.3, 5.1, 5.4_

- [x] 2. Environment variable configuration and importlib-based DAL resolution
  - [x] 2.1 Configure `DYNAMODB_TABLE_NAME` environment variable for DynamoDBCaseDAL
    - DynamoDBCaseDAL reads `DYNAMODB_TABLE_NAME` directly from `os.environ.get("DYNAMODB_TABLE_NAME", "")`
    - No AppSettings class or config.py — each DAL owns its own configuration via `os.environ`
    - _Requirements: 5.2_

  - [x] 2.2 Configure importlib-based DAL resolution in dependencies.py
    - `dependencies.py` reads `DAL_IMPLEMENTATION` env var (a fully-qualified dotted path) and dynamically imports the class using `importlib`
    - No registry, no conditional imports — resolution is purely based on the dotted path string
    - For DynamoDB: `DAL_IMPLEMENTATION = "aws_dal.dynamodb_case_dal.DynamoDBCaseDAL"`
    - _Requirements: 4.1, 4.2, 4.3, 4.5, 4.6, 4.7_

  - [x] 2.3 Write unit tests for importlib-based DAL resolution
    - Test: when `DAL_IMPLEMENTATION` is set to `aws_dal.dynamodb_case_dal.DynamoDBCaseDAL` and module is importable, `get_dal` returns `DynamoDBCaseDAL` instance
    - Test: when `DAL_IMPLEMENTATION` points to a non-importable module, `get_dal` raises `ValueError`
    - Test: when `DAL_IMPLEMENTATION` points to a module without the expected class, `get_dal` raises `ValueError`
    - Test: when `DAL_IMPLEMENTATION` is not set, defaults to `InMemoryCaseDAL`
    - _Requirements: 4.1, 4.2, 4.4, 4.5, 4.6, 4.7_

- [x] 3. Checkpoint - Validate infrastructure and registration
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. DynamoDBCaseDAL implementation
  - [x] 4.1 Create `api/aws_dal/` package with `__init__.py` and `dynamodb_case_dal.py`
    - Create `api/aws_dal/__init__.py` exporting `DynamoDBCaseDAL`
    - Create `api/aws_dal/dynamodb_case_dal.py` with class skeleton implementing `CaseDAL`
    - Add `__init__` that reads `os.environ.get("DYNAMODB_TABLE_NAME", "")` and raises `RuntimeError` if empty
    - Initialize boto3 DynamoDB resource and table reference
    - Add `_serialize` and `_deserialize` helper methods for CaseModel ↔ DynamoDB item conversion
    - _Requirements: 3.1, 3.7, 3.8, 5.2, 5.3_

  - [x] 4.2 Implement `create_case` and `get_case_by_id`
    - `create_case`: use `put_item` with `ConditionExpression="attribute_not_exists(case_id)"`, catch `ConditionalCheckFailedException` → raise `ValueError`
    - `get_case_by_id`: use `get_item`, check for `Item` key in response → raise `KeyError` if absent
    - Propagate other `ClientError` exceptions to caller
    - _Requirements: 3.2, 3.3, 3.6, 3.8, 3.9, 3.10_

  - [x] 4.3 Implement `update_case`, `delete_case`, and `get_all_cases`
    - `update_case`: use `put_item` with `ConditionExpression="attribute_exists(case_id)"`, catch `ConditionalCheckFailedException` → raise `KeyError`
    - `delete_case`: use `delete_item` with `ConditionExpression="attribute_exists(case_id)"`, catch `ConditionalCheckFailedException` → raise `KeyError`
    - `get_all_cases`: use `scan` with pagination loop on `LastEvaluatedKey`
    - Propagate other `ClientError` exceptions to caller
    - _Requirements: 3.2, 3.4, 3.5, 3.10, 3.11_

  - [x] 4.4 Write unit tests for DynamoDBCaseDAL
    - Test: missing `DYNAMODB_TABLE_NAME` raises `RuntimeError` at init
    - Test: valid `DYNAMODB_TABLE_NAME` initializes successfully
    - Test: boto3 `ClientError` propagates without being swallowed
    - Use `moto` or `unittest.mock` to mock DynamoDB
    - _Requirements: 3.7, 3.10, 5.3_

- [x] 5. Checkpoint - Validate DAL implementation
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Property-based tests for DynamoDBCaseDAL
  - [x] 6.1 Write property test for create-then-retrieve round-trip
    - **Property 1: Create-then-retrieve round-trip**
    - Reuse `valid_case_model()` strategy from existing tests
    - Use `moto` mock DynamoDB for isolated testing
    - **Validates: Requirements 3.8, 3.9**

  - [x] 6.2 Write property test for duplicate create rejection
    - **Property 2: Duplicate create rejection preserves store**
    - Verify `ValueError` raised on duplicate and original case unchanged
    - **Validates: Requirements 3.3**

  - [x] 6.3 Write property test for non-existent ID operations
    - **Property 3: Non-existent ID operations raise KeyError**
    - Verify `get_case_by_id`, `update_case`, and `delete_case` all raise `KeyError` for absent UUIDs
    - **Validates: Requirements 3.4, 3.5, 3.6**

  - [x] 6.4 Write property test for pagination completeness
    - **Property 4: Pagination returns complete results**
    - Store N distinct cases, mock scan to return paginated responses, verify all N returned
    - **Validates: Requirements 3.11**

- [x] 7. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The `api/aws_dal/` directory is a sibling package to `app/` — it must be on `sys.path` when deployed (included in the Lambda ZIP) but is absent in local dev unless `DAL_IMPLEMENTATION` is set
- Infrastructure tasks (Terraform) have no automated test runner here — validate with `terraform validate` and `terraform plan`
- `moto` library provides a local DynamoDB mock suitable for both unit and property tests
- Dependencies are split into three tiers: `requirements.txt` (core runtime), `requirements-aws.txt` (AWS runtime + core), `requirements-dev.txt` (test/dev + AWS + core). The Lambda build uses `requirements-aws.txt`; local development uses `requirements-dev.txt`.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1"] },
    { "id": 1, "tasks": ["1.2", "2.2"] },
    { "id": 2, "tasks": ["2.3", "4.1"] },
    { "id": 3, "tasks": ["4.2"] },
    { "id": 4, "tasks": ["4.3"] },
    { "id": 5, "tasks": ["4.4", "6.1", "6.2", "6.3", "6.4"] }
  ]
}
```
