from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from wodly_api.config import settings
from wodly_api.db import get_session

app = FastAPI(title="Wodly API", version="0.1.0")

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.env}


@app.get("/health/db", tags=["system"])
async def health_db(session: SessionDep) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ok"}
