"""FastAPI application for ProcessFlow AI."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from processflow.api.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    from processflow.api.database.engine import async_engine
    from processflow.api.database.migrations import create_tables

    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    await create_tables()
    logger.info("ProcessFlow API started on %s:%s", settings.host, settings.port)
    yield
    await async_engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="ProcessFlow AI API",
        description="Natural language to process flow diagrams and techno-economic analysis",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from processflow.api.routes.health import router as health_router
    from processflow.api.routes.jobs import router as jobs_router
    from processflow.api.routes.templates import router as templates_router

    app.include_router(health_router)
    app.include_router(jobs_router)
    app.include_router(templates_router)

    return app


app = create_app()


def run():
    """Entry point for the processflow-api script."""
    import uvicorn

    uvicorn.run(
        "processflow.api.app:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
