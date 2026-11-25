import asyncio
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

OWNER = "09121110001"
COACH = "09121110002"
ATH1 = "09121110003"
ATH2 = "09121110004"
OUTSIDER = "09121110005"
TEHRAN = ZoneInfo("Asia/Tehran")
FRAN = {
    "title": "Fran",
    "description": "21-15-9 Thrusters, Pull-ups",
    "score_type": "for_time",
}


def _soon() -> str:
    return (datetime.now(UTC) + timedelta(hours=2)).isoformat()


async def _box(client, login):
    owner = await login(OWNER)
    r = await client.post("/boxes", json={"name": "CrossFit Tehran"}, headers=owner)
    return owner, r.json()["box"]["id"]


async def _join(client, login, owner, box_id, phone, role):
    r = await client.post(
        f"/boxes/{box_id}/invites", json={"role": role}, headers=owner
    )
    headers = await login(phone)
    ok = await client.post(
        "/invites/redeem", json={"code": r.json()["code"]}, headers=headers
    )
    assert ok.status_code == 200
    return headers


async def _create(client, headers, box_id, **overrides):
    body = {"starts_at": _soon(), "workout": FRAN}
    body.update(overrides)
    r = await client.post(f"/boxes/{box_id}/sessions", json=body, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def _local_day(session_json) -> str:
    starts = datetime.fromisoformat(session_json["starts_at"])
    return starts.astimezone(TEHRAN).date().isoformat()


async def _list(client, headers, box_id, day):
    r = await client.get(
        f"/boxes/{box_id}/sessions", params={"date": day}, headers=headers
    )
    assert r.status_code == 200, r.text
    return r.json()


def _book_url(box_id, session_json) -> str:
    return f"/boxes/{box_id}/sessions/{session_json['id']}/book"


async def test_create_session_with_inline_workout(client, login):
    owner, box_id = await _box(client, login)
    s = await _create(client, owner, box_id, title="6 AM")
    assert s["title"] == "6 AM"
    assert s["workout"]["title"] == "Fran"
    assert (s["capacity"], s["booked_count"], s["booked_by_me"]) == (20, 0, False)


async def test_sessions_can_share_one_workout(client, login):
    owner, box_id = await _box(client, login)
    r = await client.post(f"/boxes/{box_id}/workouts", json=FRAN, headers=owner)
    assert r.status_code == 201
    workout_id = r.json()["id"]

    a = await _create(client, owner, box_id, workout_id=workout_id, workout=None)
    b = await _create(client, owner, box_id, workout_id=workout_id, workout=None)
    assert a["workout"]["id"] == b["workout"]["id"] == workout_id
    listing = await client.get(f"/boxes/{box_id}/workouts", headers=owner)
    assert len(listing.json()) == 1


async def test_workout_and_workout_id_are_exclusive(client, login):
    owner, box_id = await _box(client, login)
    r = await client.post(
        f"/boxes/{box_id}/sessions",
        json={
            "starts_at": _soon(),
            "workout": FRAN,
            "workout_id": "00000000-0000-0000-0000-000000000001",
        },
        headers=owner,
    )
    assert r.status_code == 422


async def test_naive_datetime_is_rejected(client, login):
    owner, box_id = await _box(client, login)
    r = await client.post(
        f"/boxes/{box_id}/sessions",
        json={"starts_at": "2030-01-01T10:00:00", "workout": FRAN},
        headers=owner,
    )
    assert r.status_code == 422


async def test_day_listing_uses_box_timezone(client, login):
    owner, box_id = await _box(client, login)
    today = datetime.now(TEHRAN).date()
    tomorrow = today + timedelta(days=1)
    starts = datetime.combine(tomorrow, time(0, 30), tzinfo=TEHRAN)
    await _create(client, owner, box_id, starts_at=starts.isoformat())

    assert len(await _list(client, owner, box_id, tomorrow.isoformat())) == 1
    assert await _list(client, owner, box_id, today.isoformat()) == []


async def test_athlete_cannot_create_sessions_or_workouts(client, login):
    owner, box_id = await _box(client, login)
    athlete = await _join(client, login, owner, box_id, ATH1, "athlete")

    r = await client.post(
        f"/boxes/{box_id}/sessions",
        json={"starts_at": _soon(), "workout": FRAN},
        headers=athlete,
    )
    assert r.status_code == 403
    r = await client.post(f"/boxes/{box_id}/workouts", json=FRAN, headers=athlete)
    assert r.status_code == 403


async def test_booking_and_cancelling(client, login):
    owner, box_id = await _box(client, login)
    athlete = await _join(client, login, owner, box_id, ATH1, "athlete")
    s = await _create(client, owner, box_id)
    url = _book_url(box_id, s)

    r = await client.post(url, headers=athlete)
    assert r.status_code == 201
    assert (r.json()["booked_count"], r.json()["booked_by_me"]) == (1, True)
    assert (await client.post(url, headers=athlete)).status_code == 409

    listed = (await _list(client, athlete, box_id, _local_day(s)))[0]
    assert listed["booked_by_me"] is True

    r = await client.delete(url, headers=athlete)
    assert (r.json()["booked_count"], r.json()["booked_by_me"]) == (0, False)
    assert (await client.delete(url, headers=athlete)).status_code == 404


async def test_full_session_rejects_booking(client, login):
    owner, box_id = await _box(client, login)
    a1 = await _join(client, login, owner, box_id, ATH1, "athlete")
    a2 = await _join(client, login, owner, box_id, ATH2, "athlete")
    s = await _create(client, owner, box_id, capacity=1)

    assert (await client.post(_book_url(box_id, s), headers=a1)).status_code == 201
    assert (await client.post(_book_url(box_id, s), headers=a2)).status_code == 409


async def test_concurrent_bookings_respect_capacity(client, login):
    owner, box_id = await _box(client, login)
    a1 = await _join(client, login, owner, box_id, ATH1, "athlete")
    a2 = await _join(client, login, owner, box_id, ATH2, "athlete")
    s = await _create(client, owner, box_id, capacity=1)
    url = _book_url(box_id, s)

    results = await asyncio.gather(
        client.post(url, headers=a1), client.post(url, headers=a2)
    )
    assert sorted(r.status_code for r in results) == [201, 409]


async def test_canceled_and_past_sessions_are_not_bookable(client, login):
    owner, box_id = await _box(client, login)
    athlete = await _join(client, login, owner, box_id, ATH1, "athlete")

    canceled = await _create(client, owner, box_id)
    r = await client.patch(
        f"/boxes/{box_id}/sessions/{canceled['id']}",
        json={"canceled": True},
        headers=owner,
    )
    assert r.status_code == 200 and r.json()["canceled"] is True
    assert (
        await client.post(_book_url(box_id, canceled), headers=athlete)
    ).status_code == 409

    past_start = (datetime.now(UTC) - timedelta(hours=3)).isoformat()
    past = await _create(client, owner, box_id, starts_at=past_start)
    assert (
        await client.post(_book_url(box_id, past), headers=athlete)
    ).status_code == 409


async def test_non_member_gets_404(client, login):
    _owner, box_id = await _box(client, login)
    outsider = await login(OUTSIDER)
    r = await client.get(f"/boxes/{box_id}/sessions", headers=outsider)
    assert r.status_code == 404


async def test_attendees_are_visible_to_coach_only(client, login):
    owner, box_id = await _box(client, login)
    athlete = await _join(client, login, owner, box_id, ATH1, "athlete")
    s = await _create(client, owner, box_id)
    await client.post(_book_url(box_id, s), headers=athlete)

    url = f"/boxes/{box_id}/sessions/{s['id']}/attendees"
    r = await client.get(url, headers=owner)
    assert r.status_code == 200 and len(r.json()) == 1
    assert (await client.get(url, headers=athlete)).status_code == 403


async def test_only_owner_or_session_coach_can_edit(client, login):
    owner, box_id = await _box(client, login)
    coach = await _join(client, login, owner, box_id, COACH, "coach")
    s = await _create(client, owner, box_id)
    url = f"/boxes/{box_id}/sessions/{s['id']}"

    assert (
        await client.patch(url, json={"title": "Hijacked"}, headers=coach)
    ).status_code == 403
    r = await client.patch(url, json={"workout_id": None}, headers=owner)
    assert r.status_code == 200 and r.json()["workout"] is None


async def test_capacity_cannot_drop_below_bookings(client, login):
    owner, box_id = await _box(client, login)
    a1 = await _join(client, login, owner, box_id, ATH1, "athlete")
    a2 = await _join(client, login, owner, box_id, ATH2, "athlete")
    s = await _create(client, owner, box_id, capacity=5)
    await client.post(_book_url(box_id, s), headers=a1)
    await client.post(_book_url(box_id, s), headers=a2)

    url = f"/boxes/{box_id}/sessions/{s['id']}"
    r = await client.patch(url, json={"capacity": 1}, headers=owner)
    assert r.status_code == 409
    r = await client.patch(url, json={"capacity": 2}, headers=owner)
    assert r.status_code == 200


async def test_get_single_session(client, login):
    owner, box_id = await _box(client, login)
    athlete = await _join(client, login, owner, box_id, ATH1, "athlete")
    s = await _create(client, owner, box_id)

    r = await client.get(f"/boxes/{box_id}/sessions/{s['id']}", headers=athlete)
    assert r.status_code == 200
    assert r.json()["workout"]["title"] == "Fran"

    missing = "00000000-0000-0000-0000-000000000001"
    r = await client.get(f"/boxes/{box_id}/sessions/{missing}", headers=athlete)
    assert r.status_code == 404
