from sqlalchemy import text

OWNER = "09121110001"
COACH = "09121110002"
ATHLETE = "09121110003"
OTHER = "09121110004"


async def _create_box(client, login):
    owner = await login(OWNER)
    r = await client.post("/boxes", json={"name": "CrossFit Tehran"}, headers=owner)
    assert r.status_code == 201
    return owner, r.json()["box"]["id"]


async def _invite(client, headers, box_id, role):
    r = await client.post(
        f"/boxes/{box_id}/invites", json={"role": role}, headers=headers
    )
    assert r.status_code == 201
    return r.json()["code"]


async def _join(client, login, inviter, box_id, phone, role):
    code = await _invite(client, inviter, box_id, role)
    headers = await login(phone)
    r = await client.post("/invites/redeem", json={"code": code}, headers=headers)
    assert r.status_code == 200
    assert r.json()["role"] == role
    return headers


async def test_create_box_and_list_mine(client, login):
    owner, box_id = await _create_box(client, login)
    r = await client.get("/boxes/mine", headers=owner)
    assert r.status_code == 200
    assert [(m["box"]["id"], m["role"]) for m in r.json()] == [(box_id, "owner")]


async def test_create_box_requires_auth(client):
    r = await client.post("/boxes", json={"name": "No Auth Box"})
    assert r.status_code == 401


async def test_coach_joins_and_lists_members(client, login):
    owner, box_id = await _create_box(client, login)
    coach = await _join(client, login, owner, box_id, COACH, "coach")
    await client.patch("/me", json={"full_name": "Coach Sara"}, headers=coach)

    r = await client.get(f"/boxes/{box_id}/members", headers=coach)
    assert r.status_code == 200
    members = {m["role"]: m for m in r.json()}
    assert set(members) == {"owner", "coach"}
    assert members["coach"]["full_name"] == "Coach Sara"


async def test_athlete_has_no_coach_powers(client, login):
    owner, box_id = await _create_box(client, login)
    athlete = await _join(client, login, owner, box_id, ATHLETE, "athlete")

    members = await client.get(f"/boxes/{box_id}/members", headers=athlete)
    assert members.status_code == 403
    invite = await client.post(
        f"/boxes/{box_id}/invites", json={"role": "athlete"}, headers=athlete
    )
    assert invite.status_code == 403


async def test_non_member_gets_404(client, login):
    _, box_id = await _create_box(client, login)
    outsider = await login(OTHER)
    r = await client.get(f"/boxes/{box_id}/members", headers=outsider)
    assert r.status_code == 404


async def test_coach_can_invite_athletes_but_not_coaches(client, login):
    owner, box_id = await _create_box(client, login)
    coach = await _join(client, login, owner, box_id, COACH, "coach")

    r = await client.post(
        f"/boxes/{box_id}/invites", json={"role": "coach"}, headers=coach
    )
    assert r.status_code == 403
    r = await client.post(
        f"/boxes/{box_id}/invites", json={"role": "athlete"}, headers=coach
    )
    assert r.status_code == 201


async def test_cannot_invite_as_owner(client, login):
    owner, box_id = await _create_box(client, login)
    r = await client.post(
        f"/boxes/{box_id}/invites", json={"role": "owner"}, headers=owner
    )
    assert r.status_code == 422


async def test_invite_is_single_use(client, login):
    owner, box_id = await _create_box(client, login)
    code = await _invite(client, owner, box_id, "athlete")

    first = await login(ATHLETE)
    second = await login(OTHER)
    ok = await client.post("/invites/redeem", json={"code": code}, headers=first)
    again = await client.post("/invites/redeem", json={"code": code}, headers=second)
    assert ok.status_code == 200
    assert again.status_code == 400


async def test_already_member_conflict(client, login):
    owner, box_id = await _create_box(client, login)
    code = await _invite(client, owner, box_id, "athlete")
    r = await client.post("/invites/redeem", json={"code": code}, headers=owner)
    assert r.status_code == 409


async def test_expired_invite_rejected(client, login, engine):
    owner, box_id = await _create_box(client, login)
    code = await _invite(client, owner, box_id, "athlete")
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE invites SET expires_at = now() - interval '1 day'")
        )

    athlete = await login(ATHLETE)
    r = await client.post("/invites/redeem", json={"code": code}, headers=athlete)
    assert r.status_code == 400
