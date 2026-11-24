from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="WODLY_", env_file=".env", extra="ignore"
    )
    env: str = "local"
    database_url: str = "postgresql+asyncpg://dbuser:wodly_dev@localhost:5434/wodly"


settings = Settings()
