import re
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from wodly_api.db import SessionDep
from wodly_api.deps import CoachOrOwner, CurrentUser
from wodly_api.models import Box, Invite, Membership, Role, User
from wodly_api.schemas import (
    BoxCreate,
    BoxOut,
    InviteCreate,
    InviteOut,
    MemberOut,
    MembershipOut,
)
from wodly_api.security import generate_invite_code

router = APIRouter(prefix="/boxes", tags=["boxes"])


def _make_slug(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "box"
    return f"{base}-{secrets.token_hex(3)}"


@router.post("", status_code=201)
async def create_box(
    body: BoxCreate, user: CurrentUser, session: SessionDep
) -> MembershipOut:
    box = Box(name=body.name, slug=_make_slug(body.name))
    session.add(box)
    await session.flush()
    session.add(Membership(user_id=user.id, box_id=box.id, role=Role.OWNER))
    await session.commit()
    return MembershipOut(box=BoxOut.model_validate(box), role=Role.OWNER)


@router.get("/mine")
async def my_boxes(user: CurrentUser, session: SessionDep) -> list[MembershipOut]:
    rows = await session.execute(
        select(Membership.role, Box)
        .join(Box, Box.id == Membership.box_id)
        .where(Membership.user_id == user.id)
        .order_by(Membership.created_at)
    )
    return [
        MembershipOut(box=BoxOut.model_validate(box), role=role) for role, box in rows
    ]


@router.get("/{box_id}/members")
async def list_members(
    membership: CoachOrOwner, session: SessionDep
) -> list[MemberOut]:
    rows = await session.execute(
        select(Membership.role, User)
        .join(User, User.id == Membership.user_id)
        .where(Membership.box_id == membership.box_id)
        .order_by(Membership.created_at)
    )
    return [
        MemberOut(
            user_id=user.id, full_name=user.full_name, phone=user.phone, role=role
        )
        for role, user in rows
    ]


@router.post("/{box_id}/invites", status_code=201)
async def create_invite(
    body: InviteCreate,
    user: CurrentUser,
    membership: CoachOrOwner,
    session: SessionDep,
) -> InviteOut:
    if body.role == Role.COACH and membership.role != Role.OWNER:
        raise HTTPException(status_code=403, detail="Only the owner can invite coaches")

    invite = Invite(
        box_id=membership.box_id,
        created_by=user.id,
        code=generate_invite_code(),
        role=body.role,
        label=body.label,
        expires_at=datetime.now(UTC) + timedelta(days=body.expires_in_days),
        max_uses=body.max_uses,
        uses=0,
        revoked=False,
    )
    session.add(invite)
    await session.commit()
    return InviteOut.model_validate(invite)


@router.get("/{box_id}/invites")
async def list_invites(
    user: CurrentUser, membership: CoachOrOwner, session: SessionDep
) -> list[InviteOut]:
    query = (
        select(Invite)
        .where(
            Invite.box_id == membership.box_id,
            Invite.revoked.is_(False),
            Invite.expires_at > datetime.now(UTC),
            Invite.uses < Invite.max_uses,
        )
        .order_by(Invite.created_at.desc())
    )
    if membership.role != Role.OWNER:
        query = query.where(Invite.created_by == user.id)
    rows = await session.scalars(query)
    return [InviteOut.model_validate(invite) for invite in rows]


@router.delete("/{box_id}/invites/{code}")
async def revoke_invite(
    code: str, user: CurrentUser, membership: CoachOrOwner, session: SessionDep
) -> dict[str, str]:
    invite = await session.scalar(
        select(Invite).where(
            Invite.box_id == membership.box_id, Invite.code == code.upper()
        )
    )
    if invite is None or (
        membership.role != Role.OWNER and invite.created_by != user.id
    ):
        raise HTTPException(status_code=404, detail="Invite not found")
    invite.revoked = True
    await session.commit()
    return {"status": "revoked"}
