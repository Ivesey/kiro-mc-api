from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class AppSettings(BaseSettings):
    dal_implementation: str = "InMemoryCaseDAL"
    dynamodb_table_name: str = ""
    cosmosdb_endpoint: str = ""
    cosmosdb_key: str = ""
    cosmosdb_database_name: str = "microdigitech-cases"
    cosmosdb_container_name: str = "cases"

    model_config = ConfigDict(
        env_prefix="",
        case_sensitive=False,
    )


def get_settings() -> AppSettings:
    return AppSettings()
