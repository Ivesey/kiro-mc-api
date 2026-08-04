from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class AppSettings(BaseSettings):
    dal_implementation: str = "InMemoryCaseDAL"
    dynamodb_table_name: str = ""

    model_config = ConfigDict(
        env_prefix="",
        case_sensitive=False,
    )


def get_settings() -> AppSettings:
    return AppSettings()
