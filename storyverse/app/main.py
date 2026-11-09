"""FastAPI entrypoint — StoryVerse Phase 4 internal API."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api.routes import router
from app.config import get_settings
from app.db import init_db
from app.paths import ensure_runtime_dirs
from app.queue import job_queue, requeue_orphans
from app.story.llm import inspect_llm_gates

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("storyverse")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    ensure_runtime_dirs(settings)
    await init_db()
    job_queue.start()
    await requeue_orphans()
    gate = inspect_llm_gates(settings)
    logger.info(
        "StoryVerse API ready root=%s db=%s (no ML loaded; story backend=%s)",
        settings.root,
        settings.db_path,
        gate.active_backend,
    )
    yield
    await job_queue.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.api_title,
        version=__version__,
        description=(
            "StoryVerse AI Studio — Phase 4 story/script/scenes API. "
            "Template generator by default. No ComfyUI, no model downloads, "
            "no paid APIs unless STORYVERSE_ALLOW_CLOUD_LLM=1 + key (still gated)."
        ),
        lifespan=lifespan,
    )
    app.include_router(router, prefix="/api/v1")
    return app


app = create_app()


def run() -> None:
    """CLI: python -m app.main"""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
