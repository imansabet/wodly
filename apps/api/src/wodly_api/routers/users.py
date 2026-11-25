from fastapi import APIRouter

from wodly_api.deps import CurrentUser
from wodly_api.schemas import UserOut

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
