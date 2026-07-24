from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    dal_implementation: str = "InMemoryCaseDAL"

    class Config:
        env_prefix = ""
        case_sensitive = False


def get_settings() -> AppSettings:
    return AppSettings()
