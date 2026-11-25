import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from wodly_api.models import Role
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


class ProfileUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)

    @field_validator("full_name")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()


class BoxCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)

    @field_validator("name")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()


class BoxOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str


class MembershipOut(BaseModel):
    box: BoxOut
    role: Role


class MemberOut(BaseModel):
    user_id: uuid.UUID
    full_name: str | None
    phone: str
    role: Role


class InviteCreate(BaseModel):
    role: Role
    label: str | None = Field(default=None, max_length=80)
    expires_in_days: int = Field(default=7, ge=1, le=30)
    max_uses: int = Field(default=1, ge=1, le=100)

    @field_validator("label")
    @classmethod
    def _clean_label(cls, value: str | None) -> str | None:
        return (value or "").strip() or None

    @field_validator("role")
    @classmethod
    def _not_owner(cls, value: Role) -> Role:
        if value == Role.OWNER:
            raise ValueError("cannot invite as owner")
        return value


class InviteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    role: Role
    label: str | None
    expires_at: datetime
    max_uses: int
    uses: int


class RedeemRequest(BaseModel):
    code: str

    @field_validator("code")
    @classmethod
    def _normalize(cls, value: str) -> str:
        return value.strip().upper()
