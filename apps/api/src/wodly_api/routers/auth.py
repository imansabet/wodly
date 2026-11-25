from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from wodly_api.config import settings
from wodly_api.db import SessionDep
from wodly_api.models import OtpChallenge, User
from wodly_api.schemas import OtpRequest, OtpVerify, TokenResponse
from wodly_api.security import (
    create_access_token,
    generate_otp,
    hash_otp,
    verify_otp_hash,
)
from wodly_api.sms import SmsSender, get_sms_sender

router = APIRouter(prefix="/auth", tags=["auth"])

_INVALID_CODE = HTTPException(status_code=400, detail="Invalid or expired code")


@router.post("/otp/request", status_code=202)
async def request_otp(
    body: OtpRequest,
    session: SessionDep,
    sms: Annotated[SmsSender, Depends(get_sms_sender)],
) -> dict[str, str]:
    now = datetime.now(UTC)
    last = await session.scalar(
        select(OtpChallenge)
        .where(OtpChallenge.phone == body.phone)
        .order_by(OtpChallenge.created_at.desc())
        .limit(1)
    )
    if last and (now - last.created_at).total_seconds() < settings.otp_resend_seconds:
        raise HTTPException(status_code=429, detail="Please wait before retrying")

    code = generate_otp()
    session.add(
        OtpChallenge(
            phone=body.phone,
            code_hash=hash_otp(body.phone, code),
            expires_at=now + timedelta(seconds=settings.otp_ttl_seconds),
        )
    )
    await session.commit()
    await sms.send(body.phone, f"Wodly code: {code}")
    return {"status": "sent"}


@router.post("/otp/verify")
async def verify_otp(body: OtpVerify, session: SessionDep) -> TokenResponse:
    now = datetime.now(UTC)
    challenge = await session.scalar(
        select(OtpChallenge)
        .where(
            OtpChallenge.phone == body.phone,
            OtpChallenge.consumed_at.is_(None),
            OtpChallenge.expires_at > now,
        )
        .order_by(OtpChallenge.created_at.desc())
        .limit(1)
        .with_for_update()
    )
    if challenge is None or challenge.attempts >= settings.otp_max_attempts:
        raise _INVALID_CODE

    challenge.attempts += 1
    if not verify_otp_hash(body.phone, body.code, challenge.code_hash):
        await session.commit()  # persist the failed attempt
        raise _INVALID_CODE

    challenge.consumed_at = now
    user = await session.scalar(select(User).where(User.phone == body.phone))
    if user is None:
        user = User(phone=body.phone)
        session.add(user)
    await session.commit()
    return TokenResponse(access_token=create_access_token(user.id))
