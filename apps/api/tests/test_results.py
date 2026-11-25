from datetime import UTC, datetime, timedelta

OWNER = "09121110001"
ATH1 = "09121110002"
ATH2 = "09121110003"
OUTSIDER = "09121110005"


async def _box(client, login):
    owner = await login(OWNER)
    r = await client.post("/boxes", json={"name": "CrossFit Tehran"}, headers=owner)
    return owner, r.json()["box"]["id"]


async def _join(client, login, owner, box_id, phone, name):
    r = await client.post(
        f"/boxes/{box_id}/invites", json={"role": "athlete"}, headers=owner
    )
    headers = await login(phone)
    ok = await client.post(
        "/invites/redeem", json={"code": r.json()["code"]}, headers=headers
    )
    assert ok.status_code == 200
    await client.patch("/me", json={"full_name": name}, headers=headers)
    return headers


async def _session(
    client,
    owner,
    box_id,
    *,
    score_type="for_time",
    minutes_from_now=-30,
    workout=True,
    title="Fran",
):
    when = datetime.now(UTC) + timedelta(minutes=minutes_from_now)
    body = {"starts_at": when.isoformat()}
    if workout:
        body["workout"] = {
            "title": title,
            "description": "Go fast",
            "score_type": score_type,
        }
    r = await client.post(f"/boxes/{box_id}/sessions", json=body, headers=owner)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _me(box_id, sid):
    return f"/boxes/{box_id}/sessions/{sid}/results/me"


def _board(box_id, sid):
    return f"/boxes/{box_id}/sessions/{sid}/leaderboard"


async def test_submit_and_read_back(client, login):
    owner, box_id = await _box(client, login)
    athlete = await _join(client, login, owner, box_id, ATH1, "Sara")
    sid = await _session(client, owner, box_id)

    r = await client.put(_me(box_id, sid), json={"seconds": 272}, headers=athlete)
    assert r.status_code == 200, r.text
    assert (r.json()["display"], r.json()["rx"]) == ("4:32", True)

    again = await client.get(_me(box_id, sid), headers=athlete)
    assert again.status_code == 200 and again.json()["seconds"] == 272


async def test_resubmitting_replaces_the_result(client, login):
    owner, box_id = await _box(client, login)
    athlete = await _join(client, login, owner, box_id, ATH1, "Sara")
    sid = await _session(client, owner, box_id)

    await client.put(_me(box_id, sid), json={"seconds": 300}, headers=athlete)
    await client.put(_me(box_id, sid), json={"seconds": 280}, headers=athlete)

    board = (await client.get(_board(box_id, sid), headers=athlete)).json()
    assert [e["display"] for e in board] == ["4:40"]


async def test_leaderboard_ranks_rx_first_then_score(client, login):
    owner, box_id = await _box(client, login)
    a1 = await _join(client, login, owner, box_id, ATH1, "Sara")
    a2 = await _join(client, login, owner, box_id, ATH2, "Reza")
    sid = await _session(client, owner, box_id)

    await client.put(_me(box_id, sid), json={"seconds": 300}, headers=a1)
    await client.put(_me(box_id, sid), json={"seconds": 200, "rx": False}, headers=a2)
    await client.put(_me(box_id, sid), json={"capped": True, "reps": 80}, headers=owner)

    board = (await client.get(_board(box_id, sid), headers=a1)).json()
    assert [e["display"] for e in board] == ["5:00", "CAP · 80 reps", "3:20"]
    assert [e["rank"] for e in board] == [1, 2, 3]
    assert [e["rx"] for e in board] == [True, True, False]
    assert [e["is_me"] for e in board] == [True, False, False]
    assert board[0]["full_name"] == "Sara"
    assert all("phone" not in e for e in board)


async def test_equal_scores_share_a_rank(client, login):
    owner, box_id = await _box(client, login)
    a1 = await _join(client, login, owner, box_id, ATH1, "Sara")
    a2 = await _join(client, login, owner, box_id, ATH2, "Reza")
    sid = await _session(client, owner, box_id)

    await client.put(_me(box_id, sid), json={"seconds": 300}, headers=a1)
    await client.put(_me(box_id, sid), json={"seconds": 300}, headers=a2)
    await client.put(_me(box_id, sid), json={"seconds": 400}, headers=owner)

    board = (await client.get(_board(box_id, sid), headers=owner)).json()
    assert [e["rank"] for e in board] == [1, 1, 3]


async def test_amrap_validation_and_display(client, login):
    owner, box_id = await _box(client, login)
    athlete = await _join(client, login, owner, box_id, ATH1, "Sara")
    sid = await _session(client, owner, box_id, score_type="amrap", title="Cindy")

    r = await client.put(
        _me(box_id, sid), json={"rounds": 5, "reps": 12}, headers=athlete
    )
    assert r.status_code == 200 and r.json()["display"] == "5 rds + 12"
    bad = await client.put(_me(box_id, sid), json={"seconds": 10}, headers=athlete)
    assert bad.status_code == 422


async def test_for_time_validation(client, login):
    owner, box_id = await _box(client, login)
    athlete = await _join(client, login, owner, box_id, ATH1, "Sara")
    sid = await _session(client, owner, box_id)

    for body in ({}, {"seconds": 100, "reps": 5}, {"capped": True}):
        r = await client.put(_me(box_id, sid), json=body, headers=athlete)
        assert r.status_code == 422, body


async def test_cannot_log_when_not_allowed(client, login):
    owner, box_id = await _box(client, login)
    athlete = await _join(client, login, owner, box_id, ATH1, "Sara")
    body = {"seconds": 300}

    future = await _session(client, owner, box_id, minutes_from_now=120)
    no_wod = await _session(client, owner, box_id, workout=False)
    unscored = await _session(client, owner, box_id, score_type="not_scored")
    canceled = await _session(client, owner, box_id)
    await client.patch(
        f"/boxes/{box_id}/sessions/{canceled}", json={"canceled": True}, headers=owner
    )

    for sid in (future, no_wod, unscored, canceled):
        r = await client.put(_me(box_id, sid), json=body, headers=athlete)
        assert r.status_code == 409, (sid, r.text)


async def test_delete_own_result(client, login):
    owner, box_id = await _box(client, login)
    athlete = await _join(client, login, owner, box_id, ATH1, "Sara")
    sid = await _session(client, owner, box_id)
    await client.put(_me(box_id, sid), json={"seconds": 300}, headers=athlete)

    assert (await client.delete(_me(box_id, sid), headers=athlete)).status_code == 200
    assert (await client.delete(_me(box_id, sid), headers=athlete)).status_code == 404
    assert (await client.get(_board(box_id, sid), headers=athlete)).json() == []


async def test_non_member_cannot_see_leaderboard(client, login):
    owner, box_id = await _box(client, login)
    sid = await _session(client, owner, box_id)
    outsider = await login(OUTSIDER)
    r = await client.get(_board(box_id, sid), headers=outsider)
    assert r.status_code == 404


async def test_my_results_history_is_newest_first(client, login):
    owner, box_id = await _box(client, login)
    athlete = await _join(client, login, owner, box_id, ATH1, "Sara")
    old = await _session(client, owner, box_id, minutes_from_now=-300, title="Fran")
    new = await _session(client, owner, box_id, minutes_from_now=-30, title="Grace")
    await client.put(_me(box_id, old), json={"seconds": 300}, headers=athlete)
    await client.put(_me(box_id, new), json={"seconds": 150}, headers=athlete)

    r = await client.get(f"/boxes/{box_id}/results/mine", headers=athlete)
    assert r.status_code == 200
    assert [(x["workout_title"], x["display"]) for x in r.json()] == [
        ("Grace", "2:30"),
        ("Fran", "5:00"),
    ]
