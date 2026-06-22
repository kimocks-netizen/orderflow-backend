from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_path: str = "./database/orderflow.db"
    jwt_secret: str = "orderflow-dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440


@lru_cache()
def get_settings() -> Settings:
    return Settings()
