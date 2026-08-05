import uuid

from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import (
    CosmosResourceExistsError,
    CosmosResourceNotFoundError,
)

from app.config import get_settings
from app.dal.case_dal import CaseDAL
from app.models.case import CaseModel


class CosmosDBCaseDAL(CaseDAL):
    """CaseDAL implementation backed by Azure Cosmos DB (NoSQL/SQL API)."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.cosmosdb_endpoint or not settings.cosmosdb_key:
            raise RuntimeError(
                "COSMOSDB_ENDPOINT and COSMOSDB_KEY must be set. "
                "Cannot initialize CosmosDBCaseDAL without valid connection settings."
            )
        client = CosmosClient(settings.cosmosdb_endpoint, settings.cosmosdb_key)
        database = client.get_database_client(settings.cosmosdb_database_name)
        self._container = database.get_container_client(settings.cosmosdb_container_name)

    def _serialize(self, case: CaseModel) -> dict:
        """Convert CaseModel to Cosmos DB item (id = case_id for partition key)."""
        return {
            "id": str(case.case_id),
            "case_id": str(case.case_id),
            "email": case.email,
            "issue": case.issue,
            "response": case.response,
            "severity": case.severity,
        }

    def _deserialize(self, item: dict) -> CaseModel:
        """Convert Cosmos DB item back to CaseModel."""
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
            self._container.create_item(body=item)
        except CosmosResourceExistsError:
            raise ValueError(f"Case with case_id={case.case_id} already exists")
        return case

    def update_case(self, case_id: uuid.UUID, case: CaseModel) -> CaseModel:
        item = self._serialize(case)
        # Use case_id parameter as the key, not case.case_id
        item["id"] = str(case_id)
        item["case_id"] = str(case_id)
        try:
            # Verify existence first with a point read
            self._container.read_item(
                item=str(case_id), partition_key=str(case_id)
            )
        except CosmosResourceNotFoundError:
            raise KeyError(case_id)
        # Replace the item
        self._container.replace_item(item=str(case_id), body=item)
        return case

    def delete_case(self, case_id: uuid.UUID) -> None:
        try:
            self._container.delete_item(
                item=str(case_id), partition_key=str(case_id)
            )
        except CosmosResourceNotFoundError:
            raise KeyError(case_id)

    def get_all_cases(self) -> list[CaseModel]:
        items = list(
            self._container.query_items(
                query="SELECT * FROM c",
                enable_cross_partition_query=True,
            )
        )
        return [self._deserialize(item) for item in items]

    def get_case_by_id(self, case_id: uuid.UUID) -> CaseModel:
        try:
            item = self._container.read_item(
                item=str(case_id), partition_key=str(case_id)
            )
        except CosmosResourceNotFoundError:
            raise KeyError(case_id)
        return self._deserialize(item)
