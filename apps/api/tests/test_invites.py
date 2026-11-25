OWNER = "09121110001"
COACH = "09121110002"
ATHLETE = "09121110003"


async def _setup(client, login):
    owner = await login(OWNER)
    r = await client.post("/boxes", json={"name": "CrossFit Tehran"}, headers=owner)
    return owner, r.json()["box"]["id"]


async def _make(client, headers, box_id, **body):
    r = await client.post(f"/boxes/{box_id}/invites", json=body, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


async def _join_as_coach(client, login, owner, box_id):
    invite = await _make(client, owner, box_id, role="coach")
    coach = await login(COACH)
    r = await client.post(
        "/invites/redeem", json={"code": invite["code"]}, headers=coach
    )
    assert r.status_code == 200
    return coach


async def test_label_is_trimmed_and_listed(client, login):
    owner, box_id = await _setup(client, login)
    created = await _make(client, owner, box_id, role="athlete", label="  Sara  ")
    assert created["label"] == "Sara"

    r = await client.get(f"/boxes/{box_id}/invites", headers=owner)
    assert [(i["code"], i["label"]) for i in r.json()] == [(created["code"], "Sara")]


async def test_blank_label_becomes_null(client, login):
    owner, box_id = await _setup(client, login)
    created = await _make(client, owner, box_id, role="athlete", label="   ")
    assert created["label"] is None


async def test_redeemed_invite_leaves_pending_list(client, login):
    owner, box_id = await _setup(client, login)
    invite = await _make(client, owner, box_id, role="athlete")
    athlete = await login(ATHLETE)
    await client.post("/invites/redeem", json={"code": invite["code"]}, headers=athlete)

    r = await client.get(f"/boxes/{box_id}/invites", headers=owner)
    assert r.json() == []


async def test_coach_sees_only_own_invites(client, login):
    owner, box_id = await _setup(client, login)
    coach = await _join_as_coach(client, login, owner, box_id)
    await _make(client, owner, box_id, role="athlete", label="owner's")
    mine = await _make(client, coach, box_id, role="athlete", label="coach's")

    coach_view = await client.get(f"/boxes/{box_id}/invites", headers=coach)
    assert [i["code"] for i in coach_view.json()] == [mine["code"]]
    owner_view = await client.get(f"/boxes/{box_id}/invites", headers=owner)
    assert len(owner_view.json()) == 2


async def test_revoked_invite_cannot_be_redeemed(client, login):
    owner, box_id = await _setup(client, login)
    invite = await _make(client, owner, box_id, role="athlete")

    r = await client.delete(f"/boxes/{box_id}/invites/{invite['code']}", headers=owner)
    assert r.status_code == 200

    athlete = await login(ATHLETE)
    r = await client.post(
        "/invites/redeem", json={"code": invite["code"]}, headers=athlete
    )
    assert r.status_code == 400
    listing = await client.get(f"/boxes/{box_id}/invites", headers=owner)
    assert listing.json() == []


async def test_coach_cannot_revoke_owners_invite(client, login):
    owner, box_id = await _setup(client, login)
    coach = await _join_as_coach(client, login, owner, box_id)
    invite = await _make(client, owner, box_id, role="athlete")

    r = await client.delete(f"/boxes/{box_id}/invites/{invite['code']}", headers=coach)
    assert r.status_code == 404


async def test_athlete_cannot_list_or_revoke(client, login):
    owner, box_id = await _setup(client, login)
    invite = await _make(client, owner, box_id, role="athlete")
    athlete = await login(ATHLETE)
    await client.post("/invites/redeem", json={"code": invite["code"]}, headers=athlete)

    assert (
        await client.get(f"/boxes/{box_id}/invites", headers=athlete)
    ).status_code == 403
    r = await client.delete(f"/boxes/{box_id}/invites/XXXXXXXX", headers=athlete)
    assert r.status_code == 403
