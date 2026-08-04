from typing import Type

from app.dal.case_dal import CaseDAL
from app.dal.in_memory_case_dal import InMemoryCaseDAL
from app.config import get_settings

# Registry: string identifier → concrete CaseDAL subclass
DAL_REGISTRY: dict[str, Type[CaseDAL]] = {
    "InMemoryCaseDAL": InMemoryCaseDAL,
}

# Conditionally register DynamoDBCaseDAL if the aws_dal package is available
try:
    from aws_dal.dynamodb_case_dal import DynamoDBCaseDAL
    DAL_REGISTRY["DynamoDBCaseDAL"] = DynamoDBCaseDAL
except (ImportError, AttributeError):
    pass

_dal_instance: CaseDAL | None = None


def get_dal() -> CaseDAL:
    global _dal_instance
    if _dal_instance is None:
        settings = get_settings()
        dal_name = settings.dal_implementation
        if dal_name not in DAL_REGISTRY:
            raise ValueError(
                f"Unrecognized DAL implementation: '{dal_name}'. "
                f"Registered: {list(DAL_REGISTRY.keys())}"
            )
        _dal_instance = DAL_REGISTRY[dal_name]()
    return _dal_instance


def _reset_dal() -> None:
    """Reset the cached DAL instance. Intended for testing only."""
    global _dal_instance
    _dal_instance = None
