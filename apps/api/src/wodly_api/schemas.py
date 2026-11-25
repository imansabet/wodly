import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from wodly_api.phone import normalize_phone


class OtpRequest(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def _normalize(cls, value: str) -> str:
        return normalize_phone(value)


class OtpVerify(OtpRequest):
    code: str = Field(pattern=r"^\d{6}$")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    phone: str
    full_name: str | None
