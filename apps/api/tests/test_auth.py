PHONE = "09121234567"
NORMALIZED = "+989121234567"


def _wrong(code: str) -> str:
    return "000000" if code != "000000" else "111111"


async def test_full_login_flow(client, sms):
    r = await client.post("/auth/otp/request", json={"phone": PHONE})
    assert r.status_code == 202
    assert sms.sent[0][0] == NORMALIZED

    r = await client.post(
        "/auth/otp/verify", json={"phone": PHONE, "code": sms.last_code}
    )
    assert r.status_code == 200
    token = r.json()["access_token"]

    me = await client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["phone"] == NORMALIZED


async def test_persian_digits_are_normalized(client, sms):
    await client.post("/auth/otp/request", json={"phone": "۰۹۱۲۱۲۳۴۵۶۷"})
    assert sms.sent[0][0] == NORMALIZED


async def test_wrong_code_rejected(client, sms):
    await client.post("/auth/otp/request", json={"phone": PHONE})
    r = await client.post(
        "/auth/otp/verify", json={"phone": PHONE, "code": _wrong(sms.last_code)}
    )
    assert r.status_code == 400


async def test_code_cannot_be_reused(client, sms):
    await client.post("/auth/otp/request", json={"phone": PHONE})
    payload = {"phone": PHONE, "code": sms.last_code}
    assert (await client.post("/auth/otp/verify", json=payload)).status_code == 200
    assert (await client.post("/auth/otp/verify", json=payload)).status_code == 400


async def test_resend_is_throttled(client):
    first = await client.post("/auth/otp/request", json={"phone": PHONE})
    second = await client.post("/auth/otp/request", json={"phone": PHONE})
    assert first.status_code == 202
    assert second.status_code == 429


async def test_locked_after_max_attempts(client, sms):
    await client.post("/auth/otp/request", json={"phone": PHONE})
    good = sms.last_code
    for _ in range(5):
        await client.post(
            "/auth/otp/verify", json={"phone": PHONE, "code": _wrong(good)}
        )
    r = await client.post("/auth/otp/verify", json={"phone": PHONE, "code": good})
    assert r.status_code == 400


async def test_me_requires_token(client):
    assert (await client.get("/me")).status_code == 401
    bad = await client.get("/me", headers={"Authorization": "Bearer nope"})
    assert bad.status_code == 401
