"""Health check endpoints."""

from fastapi import APIRouter, Response
from sqlalchemy import text

from app.models.base import async_session_factory

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def liveness() -> dict[str, str]:
    """Liveness probe -- always returns 200 if the process is running."""
    return {"status": "ok"}


@router.get("/readyz")
async def readiness(response: Response) -> dict[str, str]:
    """Readiness probe -- checks database connectivity."""
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        response.status_code = 503
        return {"status": "unavailable"}
