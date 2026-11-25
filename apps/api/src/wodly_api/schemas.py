import uuid
from datetime import datetime

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from wodly_api.models import Role, ScoreType
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
    timezone: str


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


class WorkoutCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=1, max_length=4000)
    score_type: ScoreType
    time_cap_seconds: int | None = Field(default=None, ge=60, le=7200)


class WorkoutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    score_type: ScoreType
    time_cap_seconds: int | None


class SessionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, max_length=120)
    starts_at: AwareDatetime
    duration_minutes: int = Field(default=60, ge=15, le=240)
    capacity: int = Field(default=20, ge=1, le=200)
    workout_id: uuid.UUID | None = None
    workout: WorkoutCreate | None = None

    @field_validator("title")
    @classmethod
    def _blank_title(cls, value: str | None) -> str | None:
        return value or None

    @model_validator(mode="after")
    def _one_workout_source(self) -> "SessionCreate":
        if self.workout_id and self.workout:
            raise ValueError("send either workout_id or workout, not both")
        return self


class SessionUpdate(BaseModel):
    """PATCH body. `workout_id: null` detaches the workout, so the endpoint
    checks `model_fields_set` to tell 'omitted' from 'null'."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, max_length=120)
    starts_at: AwareDatetime | None = None
    duration_minutes: int | None = Field(default=None, ge=15, le=240)
    capacity: int | None = Field(default=None, ge=1, le=200)
    workout_id: uuid.UUID | None = None
    canceled: bool | None = None


class SessionOut(BaseModel):
    id: uuid.UUID
    title: str | None
    starts_at: datetime
    duration_minutes: int
    capacity: int
    booked_count: int
    booked_by_me: bool
    canceled: bool
    coach_id: uuid.UUID
    coach_name: str | None
    workout: WorkoutOut | None


class AttendeeOut(BaseModel):
    user_id: uuid.UUID
    full_name: str | None
    phone: str
