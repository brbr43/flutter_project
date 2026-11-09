#!/usr/bin/env python3
"""
StoryVerse Phase 3 smoke test.

Creates a project + scene + fake job and waits for queued → running → done
WITHOUT calling ComfyUI or any ML stack.

Usage (from storyverse/ on Windows after syncing to D:\\StoryVerse\\app):

  set STORYVERSE_ROOT=D:\\StoryVerse
  .\\venv\\Scripts\\activate
  pip install -r requirements.txt
  python scripts\\smoke_test.py

Or against a running API:

  python scripts\\smoke_test.py --base-url http://127.0.0.1:8765
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path

# Allow `python scripts/smoke_test.py` from storyverse/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


async def run_inprocess(timeout_sec: float = 15.0) -> int:
    """Boot API in-process via httpx ASGITransport — no external server needed."""
    # Isolate DB under a temp root unless user already set STORYVERSE_ROOT
    tmp_root = None
    if not os.environ.get("STORYVERSE_ROOT"):
        tmp_root = tempfile.mkdtemp(prefix="storyverse-smoke-")
        os.environ["STORYVERSE_ROOT"] = tmp_root

    # Clear settings/engine caches if re-imported
    from app.config import get_settings
    from app.db import init_db, reset_engine
    from app.queue import job_queue, requeue_orphans

    get_settings.cache_clear()
    await reset_engine()

    settings = get_settings()
    print(f"[smoke] STORYVERSE_ROOT={settings.root}")
    print(f"[smoke] db={settings.db_path}")

    from fastapi import FastAPI

    from app.api.routes import router
    from app.paths import ensure_runtime_dirs

    ensure_runtime_dirs(settings)
    await init_db()
    job_queue.start()
    await requeue_orphans()

    import httpx

    # Minimal ASGI app without lifespan (worker already started above) —
    # avoids double-starting the singleton queue.
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Manual init already done; hit endpoints under /api/v1
        r = await client.get("/api/v1/health")
        r.raise_for_status()
        health = r.json()
        print(f"[smoke] health={health}")
        assert health["status"] == "ok"
        assert health["queue_worker"] == "single-in-process"

        r = await client.post(
            "/api/v1/projects",
            json={"name": "Smoke Project", "description": "Phase 3 smoke"},
        )
        r.raise_for_status()
        project = r.json()
        project_id = project["id"]
        print(f"[smoke] project id={project_id}")

        r = await client.post(
            f"/api/v1/projects/{project_id}/scenes",
            json={
                "title": "Scene 1",
                "order_index": 0,
                "script_text": "A quiet alley at dusk.",
                "prompt": "cinematic alley, dusk, soft rain",
            },
        )
        r.raise_for_status()
        scene = r.json()
        scene_id = scene["id"]
        print(f"[smoke] scene id={scene_id}")

        r = await client.post(
            f"/api/v1/projects/{project_id}/jobs",
            json={
                "job_type": "fake",
                "scene_id": scene_id,
                "payload": {"delay_sec": 0.2, "source": "smoke_test"},
            },
        )
        r.raise_for_status()
        job = r.json()
        job_id = job["id"]
        print(f"[smoke] job id={job_id} status={job['status']}")
        assert job["status"] == "queued"

        deadline = time.monotonic() + timeout_sec
        final = job
        while time.monotonic() < deadline:
            r = await client.get(f"/api/v1/jobs/{job_id}")
            r.raise_for_status()
            final = r.json()
            print(f"[smoke] poll status={final['status']}")
            if final["status"] in ("done", "failed"):
                break
            await asyncio.sleep(0.1)

        if final["status"] != "done":
            print(f"[smoke] FAIL final={final}", file=sys.stderr)
            await job_queue.stop()
            return 1

        print(f"[smoke] result={final.get('result')}")
        marker = (final.get("result") or {}).get("marker")
        if marker and not Path(marker).is_file():
            print(f"[smoke] FAIL missing marker file {marker}", file=sys.stderr)
            await job_queue.stop()
            return 1

        # Also exercise fail path quickly
        r = await client.post(
            f"/api/v1/projects/{project_id}/jobs",
            json={
                "job_type": "fake",
                "scene_id": scene_id,
                "payload": {"delay_sec": 0.05, "force_fail": True},
            },
        )
        r.raise_for_status()
        fail_id = r.json()["id"]
        deadline = time.monotonic() + timeout_sec
        fail_final = None
        while time.monotonic() < deadline:
            r = await client.get(f"/api/v1/jobs/{fail_id}")
            r.raise_for_status()
            fail_final = r.json()
            if fail_final["status"] in ("done", "failed"):
                break
            await asyncio.sleep(0.05)
        assert fail_final and fail_final["status"] == "failed"
        print(f"[smoke] fail-cycle ok job_id={fail_id}")

        r = await client.get(f"/api/v1/projects/{project_id}/scenes")
        r.raise_for_status()
        assert len(r.json()) >= 1

        print("[smoke] PASS — project + scene + fake job lifecycle (done + failed) without ML")
        await job_queue.stop()
        return 0


async def run_against_url(base_url: str, timeout_sec: float = 30.0) -> int:
    import httpx

    base = base_url.rstrip("/")
    async with httpx.AsyncClient(base_url=base, timeout=10.0) as client:
        r = await client.get("/api/v1/health")
        r.raise_for_status()
        print(f"[smoke] health={r.json()}")

        r = await client.post(
            "/api/v1/projects",
            json={"name": "Smoke Project (live)", "description": "Phase 3"},
        )
        r.raise_for_status()
        project_id = r.json()["id"]

        r = await client.post(
            f"/api/v1/projects/{project_id}/scenes",
            json={"title": "Live Scene", "script_text": "hello"},
        )
        r.raise_for_status()
        scene_id = r.json()["id"]

        r = await client.post(
            f"/api/v1/projects/{project_id}/jobs",
            json={"job_type": "fake", "scene_id": scene_id, "payload": {"delay_sec": 0.2}},
        )
        r.raise_for_status()
        job_id = r.json()["id"]

        deadline = time.monotonic() + timeout_sec
        final = None
        while time.monotonic() < deadline:
            r = await client.get(f"/api/v1/jobs/{job_id}")
            r.raise_for_status()
            final = r.json()
            print(f"[smoke] poll status={final['status']}")
            if final["status"] in ("done", "failed"):
                break
            await asyncio.sleep(0.15)

        if not final or final["status"] != "done":
            print(f"[smoke] FAIL final={final}", file=sys.stderr)
            return 1
        print("[smoke] PASS against live API")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="StoryVerse Phase 3 smoke test (no ML)")
    parser.add_argument(
        "--base-url",
        default="",
        help="If set, hit a running server (e.g. http://127.0.0.1:8765). "
        "Otherwise run in-process ASGI smoke.",
    )
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()

    if args.base_url:
        return asyncio.run(run_against_url(args.base_url, args.timeout))
    return asyncio.run(run_inprocess(args.timeout))


if __name__ == "__main__":
    raise SystemExit(main())
