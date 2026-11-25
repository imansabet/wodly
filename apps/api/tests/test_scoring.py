from decimal import Decimal
from types import SimpleNamespace

import pytest

from wodly_api.models import ScoreType
from wodly_api.scoring import ScoreError, display, normalize, rank_key, ranked

T = ScoreType


def _r(**kw):
    base = {
        "rx": True,
        "seconds": None,
        "capped": False,
        "rounds": None,
        "reps": None,
        "load_kg": None,
        "calories": None,
    }
    return SimpleNamespace(**{**base, **kw})


def test_normalize_for_time_keeps_only_seconds():
    out = normalize(T.FOR_TIME, {"seconds": 300})
    assert out == {
        "seconds": 300,
        "rounds": None,
        "reps": None,
        "load_kg": None,
        "calories": None,
        "capped": False,
    }


def test_normalize_amrap_defaults_reps_to_zero():
    assert normalize(T.AMRAP, {"rounds": 5})["reps"] == 0


def test_normalize_capped_needs_reps_not_seconds():
    assert normalize(T.FOR_TIME, {"capped": True, "reps": 80})["capped"] is True
    with pytest.raises(ScoreError):
        normalize(T.FOR_TIME, {"capped": True})
    with pytest.raises(ScoreError):
        normalize(T.FOR_TIME, {"capped": True, "reps": 80, "seconds": 600})


@pytest.mark.parametrize(
    ("score_type", "values"),
    [
        (T.FOR_TIME, {}),
        (T.FOR_TIME, {"seconds": 100, "reps": 5}),
        (T.AMRAP, {"seconds": 10}),
        (T.MAX_LOAD, {"reps": 3}),
        (T.AMRAP, {"rounds": 3, "capped": True}),
        (T.NOT_SCORED, {"seconds": 10}),
    ],
)
def test_normalize_rejects_bad_input(score_type, values):
    with pytest.raises(ScoreError):
        normalize(score_type, values)


def test_for_time_finishers_beat_capped_athletes():
    finished = _r(seconds=900)
    capped = _r(capped=True, reps=200)
    assert rank_key(T.FOR_TIME, finished) < rank_key(T.FOR_TIME, capped)


def test_rx_always_ranks_above_scaled():
    scaled_fast = _r(seconds=100, rx=False)
    rx_slow = _r(seconds=500)
    assert ranked(T.FOR_TIME, [scaled_fast, rx_slow]) == [
        (1, rx_slow),
        (2, scaled_fast),
    ]


def test_ties_share_a_rank():
    a, b, c = _r(seconds=300), _r(seconds=300), _r(seconds=400)
    assert [rank for rank, _ in ranked(T.FOR_TIME, [c, a, b])] == [1, 1, 3]


def test_amrap_orders_by_rounds_then_reps():
    low, mid, high = _r(rounds=5, reps=3), _r(rounds=5, reps=10), _r(rounds=6, reps=0)
    assert ranked(T.AMRAP, [low, high, mid]) == [(1, high), (2, mid), (3, low)]


def test_heavier_load_ranks_first():
    light, heavy = _r(load_kg=Decimal(100)), _r(load_kg=Decimal("102.5"))
    assert ranked(T.MAX_LOAD, [light, heavy])[0][1] is heavy


@pytest.mark.parametrize(
    ("score_type", "values", "expected"),
    [
        (T.FOR_TIME, {"seconds": 272}, "4:32"),
        (T.FOR_TIME, {"seconds": 3903}, "1:05:03"),
        (T.FOR_TIME, {"capped": True, "reps": 35}, "CAP · 35 reps"),
        (T.AMRAP, {"rounds": 5, "reps": 12}, "5 rds + 12"),
        (T.AMRAP, {"rounds": 7, "reps": 0}, "7 rds"),
        (T.MAX_LOAD, {"load_kg": Decimal("102.50")}, "102.5 kg"),
        (T.MAX_REPS, {"reps": 42}, "42 reps"),
        (T.CALORIES, {"calories": 85}, "85 cal"),
    ],
)
def test_display(score_type, values, expected):
    assert display(score_type, _r(**values)) == expected
