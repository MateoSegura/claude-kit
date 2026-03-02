"""FastAPI application factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.auth.router import router as auth_router
from app.config import get_settings
from app.health import router as health_router
from app.middleware.logging import setup_logging
from app.middleware.request_id import RequestIDMiddleware
from app.models.base import Base, engine
from app.telemetry.router import router as telemetry_router

DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "dashboard"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown.

    Auto-creates tables on startup for local development.
    Production PostgreSQL environments should use Alembic migrations.
    """
    settings = get_settings()
    if settings.AUTO_CREATE_TABLES or "sqlite" in str(engine.url):
        from app.auth.models import (
            APIKey,  # noqa: F401
            OAuthConnection,  # noqa: F401
            RefreshToken,  # noqa: F401
            User,  # noqa: F401
        )
        from app.telemetry.models import (
            SessionSummary,  # noqa: F401
            TelemetryEvent,  # noqa: F401
        )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIDMiddleware)

    app.include_router(health_router)
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(telemetry_router, prefix="/api/v1/telemetry", tags=["telemetry"])

    # Dashboard
    if DASHBOARD_DIR.is_dir():
        app.mount(
            "/dashboard/static",
            StaticFiles(directory=DASHBOARD_DIR / "static"),
            name="dashboard-static",
        )

        @app.get("/dashboard", include_in_schema=False)
        @app.get("/dashboard/{path:path}", include_in_schema=False)
        async def serve_dashboard(path: str = ""):
            return FileResponse(DASHBOARD_DIR / "index.html")

    return app
