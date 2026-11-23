from fastapi import FastAPI

from wodly_api.config import settings

app = FastAPI(title="Wodly API", version="0.1.0")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.env}
