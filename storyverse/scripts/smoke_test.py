#!/usr/bin/env python3
"""
StoryVerse Phase 5 smoke test.

- Phase 4 story flow (template generator, no ML weights)
- Phase 5 image_generate via a **mock ComfyUI HTTP server** (no GPU, no real ComfyUI)
- Regenerates one scene → new version; other scene assets untouched
- Character reference stub (light)

NO model downloads. NO paid APIs.

Usage (from storyverse/ — CI / cloud):

  python scripts/smoke_test.py

Against a running API (mock ComfyUI must still be reachable at
STORYVERSE_COMFYUI_BASE_URL, or use --skip-image):

  python scripts/smoke_test.py --base-url http://127.0.0.1:8765

Windows live test with real ComfyUI: see README § Windows live image test.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _start_mock_comfyui(port: int) -> tuple[threading.Thread, object]:
    """Run mock ComfyUI (scripts/mock_comfyui.py) in a daemon thread."""
    import importlib.util

    import uvicorn

    spec = importlib.util.spec_from_file_location(
        "mock_comfyui", ROOT / "scripts" / "mock_comfyui.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    app = mod.create_mock_app()

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    def _run() -> None:
        asyncio.run(server.serve())

    t = threading.Thread(target=_run, name="mock-comfyui", daemon=True)
    t.start()
    deadline = time.monotonic() + 8.0
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.05)
    else:
        raise RuntimeError(f"Mock ComfyUI failed to bind 127.0.0.1:{port}")
    return t, server


async def _wait_job(client, job_id: int, timeout_sec: float) -> dict:
    deadline = time.monotonic() + timeout_sec
    final = None
    while time.monotonic() < deadline:
        r = await client.get(f"/api/v1/jobs/{job_id}")
        r.raise_for_status()
        final = r.json()
        if final["status"] in ("done", "failed"):
            return final
        await asyncio.sleep(0.08)
    raise AssertionError(f"job {job_id} timed out; last={final}")


async def _assert_story_flow(client) -> int:
    r = await client.get("/api/v1/health")
    r.raise_for_status()
    health = r.json()
    print(f"[smoke] health={health}")
    assert health["status"] == "ok"
    assert health["story_backend"] == "template"
    assert health.get("image_engine") == "comfyui"
    assert "DreamShaper_8_pruned" in health.get("comfyui_checkpoint", "")

    r = await client.get("/api/v1/story/genres")
    r.raise_for_status()
    ids = {g["id"] for g in r.json()}
    expected = {"documentary", "hollywood", "mystery", "historical", "drama", "adventure"}
    assert expected.issubset(ids), ids

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
    assert draft["editable"] is True
    assert len(draft["scenes"]) >= 3
    print(f"[smoke] generated project_id={project_id} scenes={len(draft['scenes'])}")

    scene0 = draft["scenes"][0]
    r = await client.patch(
        f"/api/v1/scenes/{scene0['id']}",
        json={"title": "Edited Opening", "prompt": "foggy lighthouse coded light mystery"},
    )
    r.raise_for_status()
    return project_id


async def _assert_image_flow(client, project_id: int, timeout_sec: float) -> None:
    r = await client.get(f"/api/v1/projects/{project_id}/scenes")
    r.raise_for_status()
    scenes = r.json()
    assert len(scenes) >= 2
    s1, s2 = scenes[0], scenes[1]

    # Light character stub
    r = await client.post(
        f"/api/v1/projects/{project_id}/characters",
        json={
            "name": "Keeper Mira",
            "description": "weathered lighthouse keeper, grey coat",
            "visual_prompt": "woman 50s, grey wool coat, lantern",
            "reference_notes": "optional refs folder stub",
        },
    )
    r.raise_for_status()
    char = r.json()
    char_id = char["id"]
    r = await client.post(f"/api/v1/characters/{char_id}/ref-stub")
    r.raise_for_status()
    stub = r.json()
    assert stub["stub"] is True
    assert Path(stub["refs_dir"]).is_dir()
    print(f"[smoke] character stub ok id={char_id} refs={stub['refs_dir']}")

    # Generate images for two scenes (serialized by single worker)
    job_ids: list[int] = []
    for sc in (s1, s2):
        r = await client.post(
            f"/api/v1/scenes/{sc['id']}/generate-image",
            json={"character_ids": [char_id], "seed": 123, "steps": 4},
        )
        r.raise_for_status()
        out = r.json()
        assert out["job"]["job_type"] == "image_generate"
        assert out["job"]["status"] == "queued"
        job_ids.append(out["job"]["id"])
        print(f"[smoke] queued image_generate job={out['job']['id']} scene={sc['id']}")

    results = []
    for jid in job_ids:
        final = await _wait_job(client, jid, timeout_sec)
        assert final["status"] == "done", final
        assert final["result"] and final["result"].get("ok") is True
        assert final["result"].get("version") >= 1
        results.append(final)
        print(
            f"[smoke] image job done id={jid} version={final['result']['version']} "
            f"path={final['result'].get('path')}"
        )

    # Assets exist on disk
    from app.config import get_settings

    settings = get_settings()
    for final in results:
        abs_path = Path(final["result"]["absolute_path"])
        assert abs_path.is_file(), abs_path
        assert abs_path.stat().st_size > 20

    # List images for scene 1
    r = await client.get(f"/api/v1/scenes/{s1['id']}/images")
    r.raise_for_status()
    imgs1 = r.json()
    assert len(imgs1) == 1
    assert imgs1[0]["kind"] == "scene_image"
    assert imgs1[0]["meta"]["version"] == 1
    assert imgs1[0]["meta"]["checkpoint"] == "DreamShaper_8_pruned.safetensors"

    r = await client.get(f"/api/v1/scenes/{s2['id']}/images")
    r.raise_for_status()
    imgs2_before = r.json()
    assert len(imgs2_before) == 1
    s2_path_v1 = imgs2_before[0]["path"]

    # Regenerate scene 1 only — must bump to v002 without wiping scene 2
    r = await client.post(
        f"/api/v1/scenes/{s1['id']}/generate-image",
        json={"seed": 999, "steps": 4},
    )
    r.raise_for_status()
    regen_job = r.json()["job"]["id"]
    final = await _wait_job(client, regen_job, timeout_sec)
    assert final["status"] == "done", final
    assert final["result"]["version"] == 2
    print(f"[smoke] regenerate scene={s1['id']} → version=2")

    r = await client.get(f"/api/v1/scenes/{s1['id']}/images")
    r.raise_for_status()
    imgs1_after = r.json()
    assert len(imgs1_after) == 2
    versions = sorted(a["meta"]["version"] for a in imgs1_after)
    assert versions == [1, 2]

    r = await client.get(f"/api/v1/scenes/{s2['id']}/images")
    r.raise_for_status()
    imgs2_after = r.json()
    assert len(imgs2_after) == 1
    assert imgs2_after[0]["path"] == s2_path_v1
    print("[smoke] regenerate kept other scene assets intact")

    # Fake job still works
    r = await client.post(
        f"/api/v1/projects/{project_id}/jobs",
        json={"job_type": "fake", "scene_id": s1["id"], "payload": {"delay_sec": 0.05}},
    )
    r.raise_for_status()
    fake = await _wait_job(client, r.json()["id"], timeout_sec)
    assert fake["status"] == "done"

    # Reject download-style checkpoint
    r = await client.post(
        f"/api/v1/scenes/{s1['id']}/generate-image",
        json={"checkpoint": "https://example.com/model.safetensors"},
    )
    assert r.status_code == 400
    print("[smoke] rejected remote checkpoint URL")


async def run_inprocess(timeout_sec: float = 30.0) -> int:
    tmp_root = None
    if not os.environ.get("STORYVERSE_ROOT"):
        tmp_root = tempfile.mkdtemp(prefix="storyverse-smoke-")
        os.environ["STORYVERSE_ROOT"] = tmp_root

    os.environ.pop("STORYVERSE_ALLOW_LOCAL_LLM", None)
    os.environ.pop("STORYVERSE_ALLOW_CLOUD_LLM", None)
    os.environ.pop("STORYVERSE_CLOUD_LLM_API_KEY", None)

    mock_port = _free_port()
    os.environ["STORYVERSE_COMFYUI_BASE_URL"] = f"http://127.0.0.1:{mock_port}"
    print(f"[smoke] mock ComfyUI → http://127.0.0.1:{mock_port}")
    _thread, server = _start_mock_comfyui(mock_port)

    from app.config import get_settings
    from app.db import init_db, reset_engine
    from app.queue import job_queue, requeue_orphans

    get_settings.cache_clear()
    await reset_engine()

    settings = get_settings()
    print(f"[smoke] STORYVERSE_ROOT={settings.root}")
    print(f"[smoke] comfyui={settings.comfyui_base_url}")
    assert settings.comfyui_checkpoint == "DreamShaper_8_pruned.safetensors"

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
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            project_id = await _assert_story_flow(client)
            await _assert_image_flow(client, project_id, timeout_sec)
            print(
                "[smoke] PASS — story + image_generate (mock ComfyUI) + "
                "versioned regenerate (no GPU / no model download)"
            )
    finally:
        await job_queue.stop()
        server.should_exit = True
    return 0


async def run_against_url(base_url: str, timeout_sec: float = 60.0, skip_image: bool = False) -> int:
    import httpx

    base = base_url.rstrip("/")
    async with httpx.AsyncClient(base_url=base, timeout=30.0) as client:
        project_id = await _assert_story_flow(client)
        if skip_image:
            print("[smoke] PASS against live API (story only; --skip-image)")
            return 0
        await _assert_image_flow(client, project_id, timeout_sec)
        print("[smoke] PASS against live API (story + image_generate)")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="StoryVerse Phase 5 smoke (mock ComfyUI by default)"
    )
    parser.add_argument(
        "--base-url",
        default="",
        help="Hit a running server. For image jobs, ComfyUI (or mock) must match "
        "that server's STORYVERSE_COMFYUI_BASE_URL.",
    )
    parser.add_argument(
        "--skip-image",
        action="store_true",
        help="With --base-url, only run Phase 4 story checks",
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    try:
        if args.base_url:
            return asyncio.run(
                run_against_url(args.base_url, args.timeout, skip_image=args.skip_image)
            )
        return asyncio.run(run_inprocess(args.timeout))
    except Exception as exc:  # noqa: BLE001
        print(f"[smoke] FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
