from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from wodly_api.db import SessionDep
from wodly_api.deps import CurrentUser
from wodly_api.models import Box, Invite, Membership
from wodly_api.schemas import BoxOut, MembershipOut, RedeemRequest

router = APIRouter(prefix="/invites", tags=["invites"])


@router.post("/redeem")
async def redeem_invite(
    body: RedeemRequest, user: CurrentUser, session: SessionDep
) -> MembershipOut:
    invite = await session.scalar(
        select(Invite).where(Invite.code == body.code).with_for_update()
    )
    if (
        invite is None
        or invite.revoked
        or invite.expires_at <= datetime.now(UTC)
        or invite.uses >= invite.max_uses
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired invite")

    existing = await session.scalar(
        select(Membership).where(
            Membership.user_id == user.id, Membership.box_id == invite.box_id
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Already a member of this box")

    invite.uses += 1
    session.add(Membership(user_id=user.id, box_id=invite.box_id, role=invite.role))
    box = await session.get(Box, invite.box_id)
    await session.commit()
    return MembershipOut(box=BoxOut.model_validate(box), role=invite.role)
