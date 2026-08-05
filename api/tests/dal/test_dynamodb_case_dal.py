"""Unit tests for DynamoDBCaseDAL implementation."""

import os
import uuid

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws
from unittest.mock import patch, MagicMock

from aws_dal.dynamodb_case_dal import DynamoDBCaseDAL
from app.models.case import CaseModel


TABLE_NAME = "test-cases"


def _make_case(**overrides) -> CaseModel:
    """Helper to create a valid CaseModel with sensible defaults."""
    defaults = {
        "case_id": uuid.uuid4(),
        "email": "test@example.com",
        "issue": "Something broke",
        "response": "We are looking into it.",
        "severity": "medium",
    }
    defaults.update(overrides)
    return CaseModel(**defaults)


def _create_mock_table(region: str = "us-east-1") -> None:
    """Create a mock DynamoDB table for testing."""
    dynamodb = boto3.resource("dynamodb", region_name=region)
    dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[{"AttributeName": "case_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "case_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )


class TestMissingTableName:
    """Tests for missing DYNAMODB_TABLE_NAME configuration."""

    def test_missing_table_name_raises_runtime_error(self):
        """RuntimeError raised when DYNAMODB_TABLE_NAME is empty."""
        with patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": ""}):
            with pytest.raises(RuntimeError, match="DYNAMODB_TABLE_NAME"):
                DynamoDBCaseDAL()


class TestValidInitialization:
    """Tests for successful DynamoDBCaseDAL initialization."""

    @mock_aws
    def test_valid_table_name_initializes_successfully(self):
        """DAL initializes when a valid table name is configured."""
        with patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": TABLE_NAME, "AWS_DEFAULT_REGION": "us-east-1"}):
            _create_mock_table()
            dal = DynamoDBCaseDAL()
            assert dal._table is not None
            assert dal._table.table_name == TABLE_NAME


class TestClientErrorPropagation:
    """Tests that boto3 ClientError propagates without being swallowed."""

    @mock_aws
    def test_client_error_propagates_on_create(self):
        """Non-ConditionalCheckFailed ClientError propagates from create_case."""
        with patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": TABLE_NAME, "AWS_DEFAULT_REGION": "us-east-1"}):
            _create_mock_table()
            dal = DynamoDBCaseDAL()

        error_response = {
            "Error": {"Code": "InternalServerError", "Message": "Service unavailable"}
        }
        dal._table = MagicMock()
        dal._table.put_item.side_effect = ClientError(error_response, "PutItem")

        case = _make_case()
        with pytest.raises(ClientError) as exc_info:
            dal.create_case(case)

        assert exc_info.value.response["Error"]["Code"] == "InternalServerError"

    @mock_aws
    def test_client_error_propagates_on_get(self):
        """Non-ConditionalCheckFailed ClientError propagates from get_case_by_id."""
        with patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": TABLE_NAME, "AWS_DEFAULT_REGION": "us-east-1"}):
            _create_mock_table()
            dal = DynamoDBCaseDAL()

        error_response = {
            "Error": {"Code": "InternalServerError", "Message": "Service unavailable"}
        }
        dal._table = MagicMock()
        dal._table.get_item.side_effect = ClientError(error_response, "GetItem")

        with pytest.raises(ClientError) as exc_info:
            dal.get_case_by_id(uuid.uuid4())

        assert exc_info.value.response["Error"]["Code"] == "InternalServerError"

    @mock_aws
    def test_client_error_propagates_on_delete(self):
        """Non-ConditionalCheckFailed ClientError propagates from delete_case."""
        with patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": TABLE_NAME, "AWS_DEFAULT_REGION": "us-east-1"}):
            _create_mock_table()
            dal = DynamoDBCaseDAL()

        error_response = {
            "Error": {"Code": "InternalServerError", "Message": "Service unavailable"}
        }
        dal._table = MagicMock()
        dal._table.delete_item.side_effect = ClientError(error_response, "DeleteItem")

        with pytest.raises(ClientError) as exc_info:
            dal.delete_case(uuid.uuid4())

        assert exc_info.value.response["Error"]["Code"] == "InternalServerError"
