import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from wodly_api.db import SessionDep
from wodly_api.models import Membership, Role, User
from wodly_api.security import decode_access_token

_bearer = HTTPBearer(auto_error=False)

_ROLE_RANK = {Role.ATHLETE: 1, Role.COACH: 2, Role.OWNER: 3}


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    session: SessionDep,
) -> User:
    user_id = decode_access_token(credentials.credentials) if credentials else None
    user = await session.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(minimum: Role) -> Callable[..., Awaitable[Membership]]:
    """Dependency factory: caller must belong to the box in the path
    (`box_id`) with at least the given role."""

    async def dependency(
        box_id: uuid.UUID, user: CurrentUser, session: SessionDep
    ) -> Membership:
        membership = await session.scalar(
            select(Membership).where(
                Membership.user_id == user.id, Membership.box_id == box_id
            )
        )
        if membership is None:
            raise HTTPException(status_code=404, detail="Box not found")
        if _ROLE_RANK[membership.role] < _ROLE_RANK[minimum]:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return membership

    return dependency


AnyMember = Annotated[Membership, Depends(require_role(Role.ATHLETE))]
CoachOrOwner = Annotated[Membership, Depends(require_role(Role.COACH))]
OwnerOnly = Annotated[Membership, Depends(require_role(Role.OWNER))]
