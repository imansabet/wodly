"""Pure scoring logic: validation, ranking and display. No database access."""

from decimal import Decimal
from typing import Any, Protocol

from wodly_api.models import ScoreType

_FIELDS = ("seconds", "rounds", "reps", "load_kg", "calories")


class ScoreError(ValueError):
    pass


class ScoreLike(Protocol):
    rx: bool
    seconds: int | None
    capped: bool
    rounds: int | None
    reps: int | None
    load_kg: Decimal | None
    calories: int | None


def normalize(score_type: ScoreType, values: dict[str, Any]) -> dict[str, Any]:
    """Check which fields a score may carry for this workout type, and return
    exactly the five value fields plus `capped` (unused ones set to None)."""
    capped = bool(values.get("capped"))
    provided = {f for f in _FIELDS if values.get(f) is not None}

    if score_type is ScoreType.NOT_SCORED:
        raise ScoreError("This workout is not scored")
    if capped and score_type is not ScoreType.FOR_TIME:
        raise ScoreError("Only 'for time' workouts can be capped")

    if score_type is ScoreType.FOR_TIME and capped:
        required = allowed = {"reps"}
    elif score_type is ScoreType.FOR_TIME:
        required = allowed = {"seconds"}
    elif score_type is ScoreType.AMRAP:
        required, allowed = {"rounds"}, {"rounds", "reps"}
    elif score_type is ScoreType.MAX_LOAD:
        required = allowed = {"load_kg"}
    elif score_type is ScoreType.MAX_REPS:
        required = allowed = {"reps"}
    else:  # CALORIES
        required = allowed = {"calories"}

    if missing := required - provided:
        raise ScoreError(f"Missing: {', '.join(sorted(missing))}")
    if extra := provided - allowed:
        raise ScoreError(
            f"Not applicable to {score_type.value}: {', '.join(sorted(extra))}"
        )

    cleaned: dict[str, Any] = {
        f: values.get(f) if f in allowed else None for f in _FIELDS
    }
    if score_type is ScoreType.AMRAP and cleaned["reps"] is None:
        cleaned["reps"] = 0
    cleaned["capped"] = capped
    return cleaned


def rank_key(score_type: ScoreType, r: ScoreLike) -> tuple[float, ...]:
    """Smaller key = better. Only compare keys of the same score type."""
    if score_type is ScoreType.FOR_TIME:
        if r.capped:
            return (1, -(r.reps or 0))
        return (0, r.seconds or 0)
    if score_type is ScoreType.AMRAP:
        return (-(r.rounds or 0), -(r.reps or 0))
    if score_type is ScoreType.MAX_LOAD:
        return (-float(r.load_kg or 0),)
    if score_type is ScoreType.MAX_REPS:
        return (-(r.reps or 0),)
    if score_type is ScoreType.CALORIES:
        return (-(r.calories or 0),)
    return (0,)


def ranked[R: ScoreLike](
    score_type: ScoreType, results: list[R]
) -> list[tuple[int, R]]:
    """Rx before Scaled, then by score. Equal scores share a rank (1, 1, 3)."""

    def key(r: R) -> tuple[bool, tuple[float, ...]]:
        return (not r.rx, rank_key(score_type, r))

    ordered = sorted(results, key=key)
    out: list[tuple[int, R]] = []
    previous = None
    rank = 0
    for position, result in enumerate(ordered, start=1):
        if key(result) != previous:
            rank = position
            previous = key(result)
        out.append((rank, result))
    return out


def _clock(seconds: int) -> str:
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def display(score_type: ScoreType, r: ScoreLike) -> str:
    if score_type is ScoreType.FOR_TIME:
        return f"CAP · {r.reps or 0} reps" if r.capped else _clock(r.seconds or 0)
    if score_type is ScoreType.AMRAP:
        rounds = f"{r.rounds or 0} rds"
        return f"{rounds} + {r.reps}" if r.reps else rounds
    if score_type is ScoreType.MAX_LOAD:
        return f"{float(r.load_kg or 0):g} kg"
    if score_type is ScoreType.MAX_REPS:
        return f"{r.reps or 0} reps"
    if score_type is ScoreType.CALORIES:
        return f"{r.calories or 0} cal"
    return ""
