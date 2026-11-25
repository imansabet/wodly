from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from wodly_api.config import settings
from wodly_api.db import SessionDep
from wodly_api.routers import auth, boxes, invites, results, sessions, users

app = FastAPI(title="Wodly API", version="0.1.0")

if settings.env == "local":
    # Dev only: lets the Expo web build call the API from any origin.
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=".*",
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(boxes.router)
app.include_router(invites.router)
app.include_router(sessions.router)
app.include_router(results.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.env}


@app.get("/health/db", tags=["system"])
async def health_db(session: SessionDep) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "ok"}
