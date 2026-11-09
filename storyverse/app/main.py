"""FastAPI entrypoint — StoryVerse Phase 5 internal API (ComfyUI image adapter)."""

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
        "StoryVerse API ready root=%s db=%s story=%s comfyui=%s checkpoint=%s "
        "(no model downloads; single GPU-style worker)",
        settings.root,
        settings.db_path,
        gate.active_backend,
        settings.comfyui_base_url,
        settings.comfyui_checkpoint,
    )
    yield
    await job_queue.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.api_title,
        version=__version__,
        description=(
            "StoryVerse AI Studio — Phase 5 ComfyUI image adapter on Phase 4 story API. "
            "Uses existing DreamShaper_8_pruned.safetensors via local ComfyUI "
            f"({settings.comfyui_base_url}). No model downloads. No paid APIs. "
            "Single-worker queue serializes GPU jobs."
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
