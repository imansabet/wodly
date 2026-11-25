from fastapi import APIRouter

from wodly_api.db import SessionDep
from wodly_api.deps import CurrentUser
from wodly_api.schemas import ProfileUpdate, UserOut

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: ProfileUpdate, user: CurrentUser, session: SessionDep
) -> UserOut:
    user.full_name = body.full_name
    await session.commit()
    return UserOut.model_validate(user)
