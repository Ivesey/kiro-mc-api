# Requirements Document

## Introduction

This feature adds DynamoDB as a persistent backend database for the support cases API. It spans three layers: infrastructure (Terraform DynamoDB table and IAM permissions), application (a DynamoDB DAL implementation), and modularity (dynamic DAL loading via the `DAL_IMPLEMENTATION` environment variable so the DynamoDB DAL is only loaded when deployed to AWS).

## Glossary

- **Cases_Table**: The DynamoDB table that stores support case records, using on-demand billing.
- **Compute_Module**: The Terraform module at `terraform/aws/modules/compute/` that defines the Lambda function and its IAM role.
- **Lambda_Role**: The IAM execution role attached to the Lambda function.
- **DynamoDB_DAL**: A concrete implementation of the CaseDAL abstract base class that reads and writes to DynamoDB, loaded dynamically via the `DAL_IMPLEMENTATION` environment variable.
- **DAL_IMPLEMENTATION**: An environment variable containing the fully-qualified dotted path to the active CaseDAL subclass (e.g., `aws_dal.dynamodb_case_dal.DynamoDBCaseDAL`). Read by `dependencies.py` at runtime.
- **AWS_DAL_Module**: The directory at `api/aws-dal/` containing the DynamoDB DAL implementation, kept separate from the core application code for modularity.
- **Requirements_Files**: The three-tier dependency specification: `api/requirements.txt` (core runtime), `api/requirements-aws.txt` (AWS runtime, includes core), `api/requirements-dev.txt` (development and testing, includes AWS).

## Requirements

### Requirement 1: DynamoDB Table Provisioning

**User Story:** As a platform engineer, I want a DynamoDB table provisioned via Terraform, so that the API has a persistent store for support cases when deployed to AWS.

#### Acceptance Criteria

1. THE Compute_Module SHALL define a DynamoDB table resource named using the pattern `{environment}-{project_name}-cases`.
2. THE Cases_Table SHALL use `case_id` as the partition key with type String.
3. THE Cases_Table SHALL use PAY_PER_REQUEST (on-demand) billing mode.
4. THE Cases_Table SHALL be tagged with the common tags passed to the Compute_Module.
5. THE Compute_Module SHALL pass the Cases_Table name to the Lambda function as an environment variable so that the application configuration layer can resolve the table name at runtime.
6. THE Compute_Module SHALL output the Cases_Table name and ARN as module outputs so that other modules or the root configuration can reference them.

### Requirement 2: Lambda IAM Permissions for DynamoDB

**User Story:** As a platform engineer, I want the Lambda execution role to have DynamoDB permissions on the cases table, so that the application can read and write case data at runtime.

#### Acceptance Criteria

1. THE Compute_Module SHALL define a separate IAM role policy resource attached to the Lambda execution role that grants all DynamoDB actions (`dynamodb:*`) on the Cases_Table.
2. THE IAM role policy SHALL scope the Resource to both the Cases_Table ARN and the Cases_Table index ARN (i.e., `arn:...:table/<name>` and `arn:...:table/<name>/index/*`).
3. THE Compute_Module SHALL expose the Cases_Table name as a module output so it can be injected as a Lambda environment variable.
4. THE Compute_Module SHALL declare an explicit dependency between the Lambda function resource and the DynamoDB IAM role policy so that the policy is created before the function is deployed.

### Requirement 3: DynamoDB DAL Implementation

**User Story:** As a developer, I want a DynamoDB implementation of the CaseDAL abstract base class, so that support cases are persisted in DynamoDB when running on AWS.

#### Acceptance Criteria

1. THE DynamoDB_DAL SHALL reside in the AWS_DAL_Module directory at `api/aws-dal/`.
2. THE DynamoDB_DAL SHALL implement all methods defined in the CaseDAL abstract base class: create_case, update_case, delete_case, get_all_cases, and get_case_by_id, matching the method signatures and exception contracts documented in the abstract base class.
3. WHEN create_case is called with a CaseModel whose case_id already exists in the Cases_Table, THE DynamoDB_DAL SHALL raise a ValueError.
4. WHEN update_case is called with a case_id that does not exist in the Cases_Table, THE DynamoDB_DAL SHALL raise a KeyError.
5. WHEN delete_case is called with a case_id that does not exist in the Cases_Table, THE DynamoDB_DAL SHALL raise a KeyError.
6. WHEN get_case_by_id is called with a case_id that does not exist in the Cases_Table, THE DynamoDB_DAL SHALL raise a KeyError.
7. THE DynamoDB_DAL SHALL read the DynamoDB table name from the environment variable `DYNAMODB_TABLE_NAME`; IF the environment variable is not set or is empty, THEN THE DynamoDB_DAL SHALL raise a configuration error at initialization time before any database operations are attempted.
8. THE DynamoDB_DAL SHALL serialize all CaseModel fields (case_id as string, email as string, issue as string, response as string, severity as string) to DynamoDB item attributes and deserialize DynamoDB items back to CaseModel instances, preserving field types and values exactly.
9. FOR ALL valid CaseModel instances, creating a case then retrieving it by case_id SHALL return a CaseModel whose field values are equal to the original (round-trip property).
10. IF a DynamoDB service call fails due to a connectivity or service error, THEN THE DynamoDB_DAL SHALL propagate the underlying boto3 ClientError to the caller without swallowing it.
11. WHEN get_all_cases is called and the Cases_Table contains more items than a single DynamoDB scan response returns, THE DynamoDB_DAL SHALL paginate through all pages and return the complete list of CaseModel instances.

### Requirement 4: Dynamic DAL Loading (Modularity)

**User Story:** As a developer, I want the DynamoDB DAL to be loaded dynamically based on the `DAL_IMPLEMENTATION` environment variable, so that non-AWS deployments do not depend on AWS libraries and adding new backends requires no code changes to the resolution logic.

#### Acceptance Criteria

1. WHEN the `DAL_IMPLEMENTATION` environment variable is set to `aws_dal.dynamodb_case_dal.DynamoDBCaseDAL`, THE `get_dal` function in `dependencies.py` SHALL dynamically import and instantiate the DynamoDBCaseDAL class.
2. WHEN the `DAL_IMPLEMENTATION` environment variable is not set, THE `get_dal` function SHALL default to `app.dal.in_memory_case_dal.InMemoryCaseDAL`.
3. WHEN the `DAL_IMPLEMENTATION` environment variable points to a non-existent module, THE `get_dal` function SHALL raise a `ValueError` with a message that includes the module path and the underlying import error.
4. WHEN the `DAL_IMPLEMENTATION` environment variable points to a class that is not a `CaseDAL` subclass, THE `get_dal` function SHALL raise a `ValueError` indicating the class is not a valid CaseDAL implementation.
5. THE `boto3` dependency SHALL be declared in `requirements-aws.txt` (not the core `requirements.txt`), ensuring that non-AWS deployments do not pull in AWS libraries.
6. THE `dependencies.py` module SHALL NOT contain any conditional imports (try/except ImportError) or static registries — all DAL resolution SHALL be performed via `importlib` at runtime.

### Requirement 5: DynamoDB Table Name Configuration

**User Story:** As a platform engineer, I want the DynamoDB table name passed to the Lambda function as an environment variable, so that the application can locate the correct table at runtime.

#### Acceptance Criteria

1. THE Compute_Module SHALL output the Cases_Table name as a Terraform output attribute named `cases_table_name` so the root module can wire it into the Lambda environment variables.
2. THE DynamoDB_DAL SHALL read the table name directly from the `DYNAMODB_TABLE_NAME` environment variable using `os.environ.get('DYNAMODB_TABLE_NAME', '')`.
3. IF the `DYNAMODB_TABLE_NAME` environment variable is not set or is empty, THEN THE DynamoDB_DAL SHALL raise a startup exception indicating that the table name configuration is missing.
4. WHEN the root module provisions the Lambda function, THE root module SHALL include both the `cases_table_name` output from the compute module as `DYNAMODB_TABLE_NAME` and `DAL_IMPLEMENTATION` set to `aws_dal.dynamodb_case_dal.DynamoDBCaseDAL` in the Lambda environment variables.
