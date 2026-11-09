#!/usr/bin/env python3
"""
StoryVerse Phase 4 smoke test (includes Phase 3 job lifecycle).

Idea → editable JSON script/scenes via template generator.
Manual scene edit + reorder. NO ComfyUI, NO model downloads, NO paid APIs.

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


async def _assert_story_flow(client) -> int:
    """Shared Phase 4 checks. Returns project_id."""
    r = await client.get("/api/v1/health")
    r.raise_for_status()
    health = r.json()
    print(f"[smoke] health={health}")
    assert health["status"] == "ok"
    assert health["story_backend"] == "template"
    assert health.get("allow_local_llm") is False
    assert health.get("allow_cloud_llm") is False

    r = await client.get("/api/v1/story/genres")
    r.raise_for_status()
    genres = r.json()
    ids = {g["id"] for g in genres}
    expected = {"documentary", "hollywood", "mystery", "historical", "drama", "adventure"}
    assert expected.issubset(ids), ids
    print(f"[smoke] genres={sorted(ids)}")

    r = await client.get("/api/v1/story/llm-gates")
    r.raise_for_status()
    gates = r.json()
    assert gates["active_backend"] == "template"
    print(f"[smoke] llm-gates={gates['notes'][:80]}...")

    idea = "A lighthouse keeper who discovers coded lights from a vanished ship"
    r = await client.post(
        "/api/v1/story/generate",
        json={
            "idea": idea,
            "genre": "mystery",
            "true_story_mode": False,
            "language": "en",
            "preferred_backend": "template",
        },
    )
    r.raise_for_status()
    draft = r.json()
    project_id = draft["project_id"]
    print(f"[smoke] generated project_id={project_id} title={draft['title']!r}")
    assert draft["editable"] is True
    assert draft["generator"] == "template"
    assert draft["genre"] == "mystery"
    assert isinstance(draft["beats"], list) and len(draft["beats"]) >= 3
    assert isinstance(draft["scenes"], list) and len(draft["scenes"]) >= 3
    for sc in draft["scenes"]:
        for key in ("camera", "lighting", "prompt", "script_text", "content_tag", "title"):
            assert key in sc, f"missing {key} in scene"
        assert sc["content_tag"] in ("fact", "dramatization", "fiction")

    # True-story mode → fact / dramatization tags
    r = await client.post(
        "/api/v1/story/generate",
        json={
            "idea": "The 1912 sinking of a famous ocean liner and its wireless room",
            "genre": "historical",
            "true_story_mode": True,
            "project_name": "True Story Smoke",
        },
    )
    r.raise_for_status()
    true_draft = r.json()
    tags = {s["content_tag"] for s in true_draft["scenes"]}
    assert "fact" in tags or "dramatization" in tags, tags
    assert true_draft["true_story_mode"] is True
    print(f"[smoke] true-story tags={tags}")

    # Manual edit scene
    scene0 = draft["scenes"][0]
    scene_id = scene0["id"]
    r = await client.patch(
        f"/api/v1/scenes/{scene_id}",
        json={
            "title": "Edited Opening",
            "camera": "locked-off wide (edited)",
            "lighting": "moonlit fog (edited)",
            "prompt": "edited lighthouse mystery prompt",
            "script_text": "Manually rewritten beat.",
            "content_tag": "fiction",
        },
    )
    r.raise_for_status()
    edited = r.json()
    assert edited["title"] == "Edited Opening"
    assert "edited" in edited["camera"]
    print(f"[smoke] scene patched id={scene_id}")

    # Reorder: reverse
    ids_order = [s["id"] for s in draft["scenes"]]
    reversed_ids = list(reversed(ids_order))
    # After generate, scene list may still match draft; refresh
    r = await client.get(f"/api/v1/projects/{project_id}/scenes")
    r.raise_for_status()
    current_ids = [s["id"] for s in r.json()]
    reversed_ids = list(reversed(current_ids))
    r = await client.put(
        f"/api/v1/projects/{project_id}/scenes/reorder",
        json={"scene_ids": reversed_ids},
    )
    r.raise_for_status()
    reordered = r.json()
    assert [s["id"] for s in reordered] == reversed_ids
    assert [s["order_index"] for s in reordered] == list(range(len(reordered)))
    print(f"[smoke] reorder ok count={len(reordered)}")

    # Fetch full editable JSON
    r = await client.get(f"/api/v1/projects/{project_id}/story")
    r.raise_for_status()
    story = r.json()
    assert story["project_id"] == project_id
    assert len(story["scenes"]) >= 3
    print(f"[smoke] story JSON keys={sorted(story.keys())}")

    r = await client.put(
        f"/api/v1/projects/{project_id}/story",
        json={"title": "Keeper of Coded Lights", "synopsis": "Edited synopsis."},
    )
    r.raise_for_status()
    assert r.json()["title"] == "Keeper of Coded Lights"

    return project_id


async def run_inprocess(timeout_sec: float = 15.0) -> int:
    """Boot API in-process via httpx ASGITransport — no external server needed."""
    tmp_root = None
    if not os.environ.get("STORYVERSE_ROOT"):
        tmp_root = tempfile.mkdtemp(prefix="storyverse-smoke-")
        os.environ["STORYVERSE_ROOT"] = tmp_root

    # Ensure LLM flags stay off for smoke
    os.environ.pop("STORYVERSE_ALLOW_LOCAL_LLM", None)
    os.environ.pop("STORYVERSE_ALLOW_CLOUD_LLM", None)
    os.environ.pop("STORYVERSE_CLOUD_LLM_API_KEY", None)

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

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        project_id = await _assert_story_flow(client)

        # Phase 3 job lifecycle still works
        r = await client.get(f"/api/v1/projects/{project_id}/scenes")
        r.raise_for_status()
        scene_id = r.json()[0]["id"]

        r = await client.post(
            f"/api/v1/projects/{project_id}/jobs",
            json={
                "job_type": "fake",
                "scene_id": scene_id,
                "payload": {"delay_sec": 0.15, "source": "smoke_test_p4"},
            },
        )
        r.raise_for_status()
        job_id = r.json()["id"]
        deadline = time.monotonic() + timeout_sec
        final = None
        while time.monotonic() < deadline:
            r = await client.get(f"/api/v1/jobs/{job_id}")
            r.raise_for_status()
            final = r.json()
            if final["status"] in ("done", "failed"):
                break
            await asyncio.sleep(0.08)
        assert final and final["status"] == "done", final
        print(f"[smoke] fake job done id={job_id}")

        print(
            "[smoke] PASS — idea→editable JSON scenes + edit/reorder "
            "(template generator, no ML)"
        )
        await job_queue.stop()
        return 0


async def run_against_url(base_url: str, timeout_sec: float = 30.0) -> int:
    import httpx

    base = base_url.rstrip("/")
    async with httpx.AsyncClient(base_url=base, timeout=10.0) as client:
        await _assert_story_flow(client)
        print("[smoke] PASS against live API (Phase 4 story flow)")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="StoryVerse Phase 4 smoke test (no ML)")
    parser.add_argument(
        "--base-url",
        default="",
        help="If set, hit a running server (e.g. http://127.0.0.1:8765). "
        "Otherwise run in-process ASGI smoke.",
    )
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()

    try:
        if args.base_url:
            return asyncio.run(run_against_url(args.base_url, args.timeout))
        return asyncio.run(run_inprocess(args.timeout))
    except Exception as exc:  # noqa: BLE001
        print(f"[smoke] FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
