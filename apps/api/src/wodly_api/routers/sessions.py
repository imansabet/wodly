import uuid
from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from wodly_api.db import SessionDep
from wodly_api.deps import AnyMember, CoachOrOwner, CurrentUser
from wodly_api.models import Booking, Box, Role, TrainingSession, User, Workout
from wodly_api.schemas import (
    AttendeeOut,
    SessionCreate,
    SessionOut,
    SessionUpdate,
    WorkoutCreate,
    WorkoutOut,
)

router = APIRouter(prefix="/boxes/{box_id}", tags=["sessions"])


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f"{what} not found")


async def _get_workout(
    session: AsyncSession, box_id: uuid.UUID, workout_id: uuid.UUID
) -> Workout:
    workout = await session.scalar(
        select(Workout).where(Workout.id == workout_id, Workout.box_id == box_id)
    )
    if workout is None:
        raise _not_found("Workout")
    return workout


async def _get_session(
    session: AsyncSession,
    box_id: uuid.UUID,
    session_id: uuid.UUID,
    *,
    lock: bool = False,
) -> TrainingSession:
    query = select(TrainingSession).where(
        TrainingSession.id == session_id, TrainingSession.box_id == box_id
    )
    if lock:
        query = query.with_for_update()
    found = await session.scalar(query)
    if found is None:
        raise _not_found("Session")
    return found


async def _booked_count(session: AsyncSession, session_id: uuid.UUID) -> int:
    count = await session.scalar(
        select(func.count())
        .select_from(Booking)
        .where(Booking.session_id == session_id)
    )
    return count or 0


async def _load_outs(
    session: AsyncSession,
    user_id: uuid.UUID,
    where: list[ColumnElement[bool]],
) -> list[SessionOut]:
    result = await session.execute(
        select(TrainingSession, User, Workout)
        .join(User, User.id == TrainingSession.coach_id)
        .outerjoin(Workout, Workout.id == TrainingSession.workout_id)
        .where(*where)
        .order_by(TrainingSession.starts_at)
    )
    rows = result.all()

    ids = [ts.id for ts, _, _ in rows]
    counts: dict[uuid.UUID, int] = {}
    mine: set[uuid.UUID] = set()
    if ids:
        counted = await session.execute(
            select(Booking.session_id, func.count())
            .where(Booking.session_id.in_(ids))
            .group_by(Booking.session_id)
        )
        counts = {sid: n for sid, n in counted.all()}
        mine = set(
            await session.scalars(
                select(Booking.session_id).where(
                    Booking.session_id.in_(ids), Booking.user_id == user_id
                )
            )
        )

    return [
        SessionOut(
            id=ts.id,
            title=ts.title,
            starts_at=ts.starts_at,
            duration_minutes=ts.duration_minutes,
            capacity=ts.capacity,
            booked_count=counts.get(ts.id, 0),
            booked_by_me=ts.id in mine,
            canceled=ts.canceled,
            coach_id=coach.id,
            coach_name=coach.full_name,
            workout=WorkoutOut.model_validate(workout) if workout else None,
        )
        for ts, coach, workout in rows
    ]


async def _one_out(
    session: AsyncSession, user_id: uuid.UUID, session_id: uuid.UUID
) -> SessionOut:
    return (await _load_outs(session, user_id, [TrainingSession.id == session_id]))[0]


# --- workouts -------------------------------------------------------------


@router.post("/workouts", status_code=201)
async def create_workout(
    body: WorkoutCreate,
    user: CurrentUser,
    membership: CoachOrOwner,
    session: SessionDep,
) -> WorkoutOut:
    workout = Workout(box_id=membership.box_id, created_by=user.id, **body.model_dump())
    session.add(workout)
    await session.commit()
    return WorkoutOut.model_validate(workout)


@router.get("/workouts")
async def list_workouts(
    membership: CoachOrOwner, session: SessionDep
) -> list[WorkoutOut]:
    rows = await session.scalars(
        select(Workout)
        .where(Workout.box_id == membership.box_id)
        .order_by(Workout.created_at.desc())
        .limit(50)
    )
    return [WorkoutOut.model_validate(w) for w in rows]


# --- sessions -------------------------------------------------------------


@router.post("/sessions", status_code=201)
async def create_session(
    body: SessionCreate,
    user: CurrentUser,
    membership: CoachOrOwner,
    session: SessionDep,
) -> SessionOut:
    box_id = membership.box_id
    workout: Workout | None = None
    if body.workout:
        workout = Workout(
            box_id=box_id, created_by=user.id, **body.workout.model_dump()
        )
        session.add(workout)
        await session.flush()
    elif body.workout_id:
        workout = await _get_workout(session, box_id, body.workout_id)

    created = TrainingSession(
        box_id=box_id,
        coach_id=user.id,
        workout_id=workout.id if workout else None,
        title=body.title,
        starts_at=body.starts_at,
        duration_minutes=body.duration_minutes,
        capacity=body.capacity,
        canceled=False,
    )
    session.add(created)
    await session.commit()
    return await _one_out(session, user.id, created.id)


@router.get("/sessions")
async def list_sessions(
    membership: AnyMember,
    user: CurrentUser,
    session: SessionDep,
    day: Annotated[date | None, Query(alias="date")] = None,
) -> list[SessionOut]:
    """Sessions of one calendar day in the box's timezone (default: today)."""
    box = await session.get(Box, membership.box_id)
    assert box is not None
    tz = ZoneInfo(box.timezone)
    local_day = day or datetime.now(tz).date()
    start = datetime.combine(local_day, time.min, tzinfo=tz)
    end = datetime.combine(local_day + timedelta(days=1), time.min, tzinfo=tz)
    return await _load_outs(
        session,
        user.id,
        [
            TrainingSession.box_id == membership.box_id,
            TrainingSession.starts_at >= start,
            TrainingSession.starts_at < end,
        ],
    )


@router.patch("/sessions/{session_id}")
async def update_session(
    session_id: uuid.UUID,
    body: SessionUpdate,
    user: CurrentUser,
    membership: CoachOrOwner,
    session: SessionDep,
) -> SessionOut:
    target = await _get_session(session, membership.box_id, session_id, lock=True)
    if membership.role != Role.OWNER and target.coach_id != user.id:
        raise HTTPException(status_code=403, detail="Not your session")

    fields = body.model_fields_set
    if "title" in fields:
        target.title = body.title or None
    if "workout_id" in fields:
        if body.workout_id is None:
            target.workout_id = None
        else:
            await _get_workout(session, membership.box_id, body.workout_id)
            target.workout_id = body.workout_id
    if body.starts_at is not None:
        target.starts_at = body.starts_at
    if body.duration_minutes is not None:
        target.duration_minutes = body.duration_minutes
    if body.capacity is not None:
        if body.capacity < await _booked_count(session, target.id):
            raise HTTPException(
                status_code=409, detail="Capacity is below current bookings"
            )
        target.capacity = body.capacity
    if body.canceled is not None:
        target.canceled = body.canceled

    await session.commit()
    return await _one_out(session, user.id, target.id)


# --- bookings -------------------------------------------------------------


@router.post("/sessions/{session_id}/book", status_code=201)
async def book_session(
    session_id: uuid.UUID,
    user: CurrentUser,
    membership: AnyMember,
    session: SessionDep,
) -> SessionOut:
    # The row lock serializes concurrent bookings, so capacity is never exceeded.
    target = await _get_session(session, membership.box_id, session_id, lock=True)
    ends_at = target.starts_at + timedelta(minutes=target.duration_minutes)
    if target.canceled:
        raise HTTPException(status_code=409, detail="Session is canceled")
    if ends_at <= datetime.now(UTC):
        raise HTTPException(status_code=409, detail="Session is over")

    already = await session.scalar(
        select(Booking.id).where(
            Booking.session_id == target.id, Booking.user_id == user.id
        )
    )
    if already:
        raise HTTPException(status_code=409, detail="Already booked")
    if await _booked_count(session, target.id) >= target.capacity:
        raise HTTPException(status_code=409, detail="Session is full")

    session.add(Booking(session_id=target.id, user_id=user.id))
    await session.commit()
    return await _one_out(session, user.id, target.id)


@router.delete("/sessions/{session_id}/book")
async def cancel_booking(
    session_id: uuid.UUID,
    user: CurrentUser,
    membership: AnyMember,
    session: SessionDep,
) -> SessionOut:
    target = await _get_session(session, membership.box_id, session_id, lock=True)
    booking = await session.scalar(
        select(Booking).where(
            Booking.session_id == target.id, Booking.user_id == user.id
        )
    )
    if booking is None:
        raise _not_found("Booking")
    await session.delete(booking)
    await session.commit()
    return await _one_out(session, user.id, target.id)


@router.get("/sessions/{session_id}/attendees")
async def list_attendees(
    session_id: uuid.UUID, membership: CoachOrOwner, session: SessionDep
) -> list[AttendeeOut]:
    target = await _get_session(session, membership.box_id, session_id)
    rows = await session.scalars(
        select(User)
        .join(Booking, Booking.user_id == User.id)
        .where(Booking.session_id == target.id)
        .order_by(Booking.created_at)
    )
    return [
        AttendeeOut(user_id=u.id, full_name=u.full_name, phone=u.phone) for u in rows
    ]
