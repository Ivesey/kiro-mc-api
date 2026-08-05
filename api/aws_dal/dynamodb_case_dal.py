import os
import uuid

import boto3
from botocore.exceptions import ClientError

from app.dal.case_dal import CaseDAL
from app.models.case import CaseModel


class DynamoDBCaseDAL(CaseDAL):
    """CaseDAL implementation backed by AWS DynamoDB."""

    def __init__(self) -> None:
        table_name = os.environ.get("DYNAMODB_TABLE_NAME", "")
        if not table_name:
            raise RuntimeError(
                "DYNAMODB_TABLE_NAME environment variable is not set or is empty. "
                "Cannot initialize DynamoDBCaseDAL without a valid table name."
            )
        dynamodb = boto3.resource("dynamodb")
        self._table = dynamodb.Table(table_name)

    def _serialize(self, case: CaseModel) -> dict:
        """Convert a CaseModel instance to a DynamoDB item dict (all string attributes)."""
        return {
            "case_id": str(case.case_id),
            "email": case.email,
            "issue": case.issue,
            "response": case.response,
            "severity": case.severity,
        }

    def _deserialize(self, item: dict) -> CaseModel:
        """Convert a DynamoDB item dict back to a CaseModel instance."""
        return CaseModel(
            case_id=uuid.UUID(item["case_id"]),
            email=item["email"],
            issue=item["issue"],
            response=item["response"],
            severity=item["severity"],
        )

    def create_case(self, case: CaseModel) -> CaseModel:
        item = self._serialize(case)
        try:
            self._table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(case_id)",
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise ValueError(f"Case with case_id={case.case_id} already exists")
            raise
        return case

    def update_case(self, case_id: uuid.UUID, case: CaseModel) -> CaseModel:
        item = self._serialize(case)
        # Use the case_id parameter as the key, not case.case_id
        item["case_id"] = str(case_id)
        try:
            self._table.put_item(
                Item=item,
                ConditionExpression="attribute_exists(case_id)",
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise KeyError(case_id)
            raise
        return case

    def delete_case(self, case_id: uuid.UUID) -> None:
        try:
            self._table.delete_item(
                Key={"case_id": str(case_id)},
                ConditionExpression="attribute_exists(case_id)",
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise KeyError(case_id)
            raise

    def get_all_cases(self) -> list[CaseModel]:
        items: list[dict] = []
        response = self._table.scan()
        items.extend(response.get("Items", []))
        while "LastEvaluatedKey" in response:
            response = self._table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))
        return [self._deserialize(item) for item in items]

    def get_case_by_id(self, case_id: uuid.UUID) -> CaseModel:
        response = self._table.get_item(Key={"case_id": str(case_id)})
        if "Item" not in response:
            raise KeyError(case_id)
        return self._deserialize(response["Item"])
