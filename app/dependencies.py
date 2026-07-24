from typing import Type

from app.dal.case_dal import CaseDAL
from app.dal.in_memory_case_dal import InMemoryCaseDAL
from app.config import get_settings

# Registry: string identifier → concrete CaseDAL subclass
DAL_REGISTRY: dict[str, Type[CaseDAL]] = {
    "InMemoryCaseDAL": InMemoryCaseDAL,
}


def get_dal() -> CaseDAL:
    settings = get_settings()
    dal_name = settings.dal_implementation
    if dal_name not in DAL_REGISTRY:
        raise ValueError(
            f"Unrecognized DAL implementation: '{dal_name}'. "
            f"Registered: {list(DAL_REGISTRY.keys())}"
        )
    return DAL_REGISTRY[dal_name]()
