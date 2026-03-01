"""FastAPI application factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.config import get_settings
from app.health import router as health_router
from app.middleware.logging import setup_logging
from app.middleware.request_id import RequestIDMiddleware
from app.models.base import engine
from app.telemetry.router import router as telemetry_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown."""
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        lifespan=lifespan,
    )

    setup_logging(settings.LOG_LEVEL)

    app.add_middleware(RequestIDMiddleware)

    app.include_router(health_router)
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(telemetry_router, prefix="/api/v1/telemetry", tags=["telemetry"])

    return app
