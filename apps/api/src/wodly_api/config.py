from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET = "dev-only-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="WODLY_", env_file=".env", extra="ignore"
    )
    env: str = "local"
    database_url: str = "postgresql+asyncpg://dbuser:wodly_dev@localhost:5434/wodly"

    jwt_secret: str = _DEV_SECRET
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60

    otp_pepper: str = _DEV_SECRET
    otp_ttl_seconds: int = 300
    otp_max_attempts: int = 5
    otp_resend_seconds: int = 60

    @model_validator(mode="after")
    def _require_real_secrets(self) -> Self:
        if self.env != "local" and _DEV_SECRET in (self.jwt_secret, self.otp_pepper):
            raise ValueError("Set WODLY_JWT_SECRET and WODLY_OTP_PEPPER outside local")
        return self


settings = Settings()
