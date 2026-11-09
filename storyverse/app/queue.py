"""Single-worker in-process job queue.

Only one heavy job runs at a time — Phase 1 GPU policy (serialize GPU work).
Supports:
  - fake           → Phase 3 marker file (no ML)
  - image_generate → Phase 5 ComfyUI adapter (one scene; versions kept)
  - video_generate → Phase 6 clip adapter (FFmpeg fallback by default; AI gated)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select

from app.config import get_settings
from app.db import get_session_factory
from app.models import Job

logger = logging.getLogger("storyverse.queue")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JobQueue:
    """FIFO asyncio queue + one background worker coroutine."""

    def __init__(self) -> None:
        self._q: asyncio.Queue[int] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task[None]] = None
        self._running = False
        self._current_job_id: Optional[int] = None

    @property
    def current_job_id(self) -> Optional[int]:
        return self._current_job_id

    @property
    def pending_count(self) -> int:
        return self._q.qsize()

    def start(self) -> None:
        if self._worker_task is None or self._worker_task.done():
            self._running = True
            self._worker_task = asyncio.create_task(self._worker_loop(), name="storyverse-job-worker")
            logger.info("Job worker started (single in-process worker)")

    async def stop(self) -> None:
        self._running = False
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        self._worker_task = None
        logger.info("Job worker stopped")

    async def enqueue(self, job_id: int) -> None:
        await self._q.put(job_id)
        logger.info("Enqueued job_id=%s (pending=%s)", job_id, self._q.qsize())

    async def _worker_loop(self) -> None:
        while self._running:
            try:
                job_id = await self._q.get()
            except asyncio.CancelledError:
                break
            self._current_job_id = job_id
            try:
                await self._process_job(job_id)
            except Exception:  # noqa: BLE001 — isolate worker from crashes
                logger.exception("Unhandled error processing job_id=%s", job_id)
            finally:
                self._current_job_id = None
                self._q.task_done()

    async def _process_job(self, job_id: int) -> None:
        factory = get_session_factory()
        settings = get_settings()

        async with factory() as session:
            job = await session.get(Job, job_id)
            if job is None:
                logger.warning("Job %s missing; skipping", job_id)
                return
            if job.status not in ("queued",):
                logger.info("Job %s status=%s; not processing", job_id, job.status)
                return

            job.status = "running"
            job.started_at = utcnow()
            job.error_message = None
            await session.commit()

            payload: dict[str, Any] = dict(job.payload or {})
            job_type = job.job_type
            project_id = job.project_id
            scene_id = job.scene_id
            force_fail = bool(payload.get("force_fail"))

        try:
            if force_fail:
                raise RuntimeError(payload.get("fail_message", "Forced fake failure"))

            if job_type == "image_generate":
                result = await self._run_image_generate(
                    job_id=job_id,
                    project_id=project_id,
                    scene_id=scene_id,
                    payload=payload,
                    settings=settings,
                )
            elif job_type == "video_generate":
                result = await self._run_video_generate(
                    job_id=job_id,
                    project_id=project_id,
                    scene_id=scene_id,
                    payload=payload,
                    settings=settings,
                )
            elif job_type == "fake":
                result = await self._run_fake(
                    job_id=job_id,
                    job_type=job_type,
                    project_id=project_id,
                    payload=payload,
                    settings=settings,
                )
            else:
                raise RuntimeError(
                    f"Unknown job_type={job_type!r}. "
                    "Phase 6 supports: fake, image_generate, video_generate"
                )

            async with factory() as session:
                job = await session.get(Job, job_id)
                if job is None:
                    return
                job.status = "done"
                job.result = result
                job.error_message = None
                job.finished_at = utcnow()
                await session.commit()

        except Exception as exc:  # noqa: BLE001
            async with factory() as session:
                job = await session.get(Job, job_id)
                if job is None:
                    return
                job.status = "failed"
                job.result = {"ok": False}
                job.error_message = str(exc)
                job.finished_at = utcnow()
                await session.commit()
            logger.warning("Job %s failed: %s", job_id, exc)

    async def _run_fake(
        self,
        *,
        job_id: int,
        job_type: str,
        project_id: int,
        payload: dict[str, Any],
        settings: Any,
    ) -> dict[str, Any]:
        from app.paths import ensure_project_layout

        delay = float(payload.get("delay_sec", settings.fake_job_delay_sec))
        await asyncio.sleep(max(0.0, delay))
        layout = ensure_project_layout(project_id, settings)
        marker = layout["scratch"] / f"job_{job_id}.done"
        marker.write_text(
            f"job_type={job_type}\nstatus=done\n",
            encoding="utf-8",
        )
        return {
            "ok": True,
            "job_type": job_type,
            "marker": str(marker),
            "note": "Phase 3 fake job — no ComfyUI/ML invoked",
        }

    async def _run_image_generate(
        self,
        *,
        job_id: int,
        project_id: int,
        scene_id: Optional[int],
        payload: dict[str, Any],
        settings: Any,
    ) -> dict[str, Any]:
        if scene_id is None:
            raise RuntimeError("image_generate requires scene_id")

        from app.image.adapter import generate_scene_image
        from app.image.comfyui import ComfyUIClient

        client = ComfyUIClient(
            settings.comfyui_base_url,
            timeout_sec=settings.comfyui_timeout_sec,
            poll_interval_sec=settings.comfyui_poll_interval_sec,
        )
        factory = get_session_factory()
        async with factory() as session:
            return await generate_scene_image(
                session,
                project_id=project_id,
                scene_id=scene_id,
                job_id=job_id,
                payload=payload,
                settings=settings,
                client=client,
            )

    async def _run_video_generate(
        self,
        *,
        job_id: int,
        project_id: int,
        scene_id: Optional[int],
        payload: dict[str, Any],
        settings: Any,
    ) -> dict[str, Any]:
        if scene_id is None:
            raise RuntimeError("video_generate requires scene_id")

        from app.video.adapter import generate_scene_clip

        factory = get_session_factory()
        async with factory() as session:
            return await generate_scene_clip(
                session,
                project_id=project_id,
                scene_id=scene_id,
                job_id=job_id,
                payload=payload,
                settings=settings,
            )


# Process-wide singleton (one GPU-style worker for the API process)
job_queue = JobQueue()


async def requeue_orphans() -> int:
    """On startup, re-enqueue jobs left in queued/running (crash recovery → queued)."""
    factory = get_session_factory()
    count = 0
    async with factory() as session:
        result = await session.execute(
            select(Job).where(Job.status.in_(("queued", "running"))).order_by(Job.id)
        )
        jobs = list(result.scalars())
        for job in jobs:
            if job.status == "running":
                job.status = "queued"
                job.started_at = None
                job.error_message = "Reset after worker restart"
            count += 1
        await session.commit()
        for job in jobs:
            await job_queue.enqueue(job.id)
    if count:
        logger.info("Re-queued %s orphan job(s)", count)
    return count
