import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from wodly_api.db import SessionDep
from wodly_api.deps import AnyMember, CurrentUser
from wodly_api.models import Result, ScoreType, TrainingSession, User, Workout
from wodly_api.routers.sessions import get_session_or_404
from wodly_api.schemas import LeaderboardEntry, MyResultOut, ResultIn, ResultOut
from wodly_api.scoring import ScoreError, display, normalize, ranked

router = APIRouter(prefix="/boxes/{box_id}", tags=["results"])


def _out(result: Result, score_type: ScoreType) -> ResultOut:
    return ResultOut(
        session_id=result.session_id,
        rx=result.rx,
        seconds=result.seconds,
        capped=result.capped,
        rounds=result.rounds,
        reps=result.reps,
        load_kg=float(result.load_kg) if result.load_kg is not None else None,
        calories=result.calories,
        notes=result.notes,
        display=display(score_type, result),
    )


async def _find_result(session, session_id: uuid.UUID, user_id: uuid.UUID):
    return await session.scalar(
        select(Result).where(Result.session_id == session_id, Result.user_id == user_id)
    )


@router.put("/sessions/{session_id}/results/me")
async def save_my_result(
    session_id: uuid.UUID,
    body: ResultIn,
    user: CurrentUser,
    membership: AnyMember,
    session: SessionDep,
) -> ResultOut:
    target = await get_session_or_404(session, membership.box_id, session_id)
    if target.canceled:
        raise HTTPException(status_code=409, detail="Session is canceled")
    if target.workout_id is None:
        raise HTTPException(
            status_code=409, detail="No workout posted for this session"
        )
    if target.starts_at > datetime.now(UTC):
        raise HTTPException(status_code=409, detail="Session has not started yet")

    workout = await session.get(Workout, target.workout_id)
    assert workout is not None
    if workout.score_type is ScoreType.NOT_SCORED:
        raise HTTPException(status_code=409, detail="This workout is not scored")
    try:
        fields = normalize(workout.score_type, body.model_dump())
    except ScoreError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    result = await _find_result(session, target.id, user.id)
    if result is None:
        result = Result(
            box_id=membership.box_id,
            session_id=target.id,
            user_id=user.id,
            workout_id=workout.id,
        )
        session.add(result)
    result.workout_id = workout.id
    result.rx = body.rx
    result.notes = body.notes
    for name, value in fields.items():
        setattr(result, name, value)

    await session.commit()
    return _out(result, workout.score_type)


@router.get("/sessions/{session_id}/results/me")
async def read_my_result(
    session_id: uuid.UUID,
    user: CurrentUser,
    membership: AnyMember,
    session: SessionDep,
) -> ResultOut:
    target = await get_session_or_404(session, membership.box_id, session_id)
    result = await _find_result(session, target.id, user.id)
    if result is None or target.workout_id != result.workout_id:
        raise HTTPException(status_code=404, detail="Result not found")
    workout = await session.get(Workout, result.workout_id)
    assert workout is not None
    return _out(result, workout.score_type)


@router.delete("/sessions/{session_id}/results/me")
async def delete_my_result(
    session_id: uuid.UUID,
    user: CurrentUser,
    membership: AnyMember,
    session: SessionDep,
) -> dict[str, str]:
    target = await get_session_or_404(session, membership.box_id, session_id)
    result = await _find_result(session, target.id, user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")
    await session.delete(result)
    await session.commit()
    return {"status": "deleted"}


@router.get("/sessions/{session_id}/leaderboard")
async def leaderboard(
    session_id: uuid.UUID,
    user: CurrentUser,
    membership: AnyMember,
    session: SessionDep,
) -> list[LeaderboardEntry]:
    target = await get_session_or_404(session, membership.box_id, session_id)
    if target.workout_id is None:
        return []
    workout = await session.get(Workout, target.workout_id)
    assert workout is not None

    rows = (
        await session.execute(
            select(Result, User)
            .join(User, User.id == Result.user_id)
            .where(
                Result.session_id == target.id,
                Result.workout_id == target.workout_id,
            )
        )
    ).all()
    names = {result.id: person.full_name for result, person in rows}

    return [
        LeaderboardEntry(
            rank=rank,
            user_id=result.user_id,
            full_name=names[result.id],
            rx=result.rx,
            display=display(workout.score_type, result),
            notes=result.notes,
            is_me=result.user_id == user.id,
        )
        for rank, result in ranked(workout.score_type, [r for r, _ in rows])
    ]


@router.get("/results/mine")
async def my_results(
    user: CurrentUser, membership: AnyMember, session: SessionDep
) -> list[MyResultOut]:
    rows = (
        await session.execute(
            select(Result, TrainingSession, Workout)
            .join(TrainingSession, TrainingSession.id == Result.session_id)
            .join(Workout, Workout.id == Result.workout_id)
            .where(Result.user_id == user.id, Result.box_id == membership.box_id)
            .order_by(TrainingSession.starts_at.desc())
            .limit(100)
        )
    ).all()
    return [
        MyResultOut(
            **_out(result, workout.score_type).model_dump(),
            workout_title=workout.title,
            score_type=workout.score_type,
            starts_at=ts.starts_at,
        )
        for result, ts, workout in rows
    ]
