import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Role(enum.StrEnum):
    OWNER = "owner"
    COACH = "coach"
    ATHLETE = "athlete"


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(primary_key=True, default=uuid.uuid4)


def _created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _uuid_pk()
    phone: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = _created_at()


class Box(Base):
    __tablename__ = "boxes"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    timezone: Mapped[str] = mapped_column(
        String(64), default="Asia/Tehran", server_default="Asia/Tehran"
    )
    created_at: Mapped[datetime] = _created_at()


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("user_id", "box_id"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    box_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("boxes.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False, length=16))
    created_at: Mapped[datetime] = _created_at()


class Invite(Base):
    __tablename__ = "invites"

    id: Mapped[uuid.UUID] = _uuid_pk()
    box_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("boxes.id", ondelete="CASCADE"), index=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False, length=16))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    max_uses: Mapped[int] = mapped_column(Integer, default=1)
    uses: Mapped[int] = mapped_column(Integer, default=0)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    label: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = _created_at()


class OtpChallenge(Base):
    __tablename__ = "otp_challenges"

    id: Mapped[uuid.UUID] = _uuid_pk()
    phone: Mapped[str] = mapped_column(String(16), index=True)
    code_hash: Mapped[str] = mapped_column(String(128))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _created_at()


class ScoreType(enum.StrEnum):
    FOR_TIME = "for_time"
    AMRAP = "amrap"
    MAX_LOAD = "max_load"
    MAX_REPS = "max_reps"
    CALORIES = "calories"
    NOT_SCORED = "not_scored"


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[uuid.UUID] = _uuid_pk()
    box_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("boxes.id", ondelete="CASCADE"), index=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    score_type: Mapped[ScoreType] = mapped_column(
        Enum(ScoreType, native_enum=False, length=16)
    )
    time_cap_seconds: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = _created_at()


class TrainingSession(Base):
    __tablename__ = "training_sessions"
    __table_args__ = (Index("ix_training_sessions_box_starts", "box_id", "starts_at"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    box_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("boxes.id", ondelete="CASCADE")
    )
    coach_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    workout_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workouts.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str | None] = mapped_column(String(120))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    capacity: Mapped[int] = mapped_column(Integer, default=20)
    canceled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = _created_at()


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (UniqueConstraint("session_id", "user_id"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("training_sessions.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = _created_at()
