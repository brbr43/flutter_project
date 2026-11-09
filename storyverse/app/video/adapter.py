"""High-level scene clip generation: adapters → versioned project assets.

Regenerating one scene adds a new clip version; prior versions and other scenes
are kept. Default engine is FFmpeg Ken Burns (fallback, not AI).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.image.adapter import ASSET_KIND_SCENE_IMAGE, scene_image_dir
from app.models import Asset, Scene, utcnow
from app.paths import ensure_project_layout
from app.video.comfyui_i2v import AIVideoNotApprovedError, run_comfyui_i2v_stub
from app.video.ffmpeg_fallback import (
    still_to_mp4_kenburns,
    write_minimal_mock_mp4,
)
from app.video.gates import AI_VIDEO_ENGINES, FALLBACK_ENGINES, assert_no_download_urls, inspect_video_gates

logger = logging.getLogger("storyverse.video")

ASSET_KIND_SCENE_CLIP = "scene_clip"

_CLIP_VERSION_RE = re.compile(r"^v(\d{3})\.mp4$", re.IGNORECASE)


def scene_clip_dir(project_id: int, scene_id: int, settings: Settings | None = None) -> Path:
    layout = ensure_project_layout(project_id, settings)
    path = layout["assets"] / "scenes" / str(scene_id) / "clips"
    path.mkdir(parents=True, exist_ok=True)
    return path


def next_clip_version(directory: Path) -> int:
    highest = 0
    if directory.is_dir():
        for p in directory.iterdir():
            m = _CLIP_VERSION_RE.match(p.name)
            if m:
                highest = max(highest, int(m.group(1)))
    return highest + 1


def resolve_source_still(
    *,
    project_id: int,
    scene_id: int,
    payload: dict[str, Any],
    settings: Settings,
    latest_image_asset: Asset | None,
) -> Path | None:
    """Pick a still for I2V / Ken Burns: override path, else latest scene_image."""
    override = payload.get("source_image_path")
    if override:
        assert_no_download_urls(str(override), field="source_image_path")
        p = Path(str(override)).expanduser()
        if not p.is_file():
            # Also try relative to STORYVERSE_ROOT
            alt = settings.root / str(override)
            if alt.is_file():
                return alt
            raise RuntimeError(f"source_image_path not found: {override}")
        return p

    if latest_image_asset is not None:
        meta = latest_image_asset.meta or {}
        abs_path = meta.get("absolute_path")
        if abs_path and Path(str(abs_path)).is_file():
            return Path(str(abs_path))
        rel = latest_image_asset.path
        cand = settings.root / rel
        if cand.is_file():
            return cand
        # Common layout: assets/scenes/{id}/vNNN.png under projects/
        img_dir = scene_image_dir(project_id, scene_id, settings)
        name = Path(rel).name
        if (img_dir / name).is_file():
            return img_dir / name

    # Last resort: highest vNNN.png in scene image dir
    img_dir = scene_image_dir(project_id, scene_id, settings)
    versions = sorted(img_dir.glob("v*.png"))
    if versions:
        return versions[-1]
    return None


async def _latest_scene_image(session: AsyncSession, scene_id: int) -> Asset | None:
    result = await session.execute(
        select(Asset)
        .where(Asset.scene_id == scene_id, Asset.kind == ASSET_KIND_SCENE_IMAGE)
        .order_by(Asset.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def generate_scene_clip(
    session: AsyncSession,
    *,
    project_id: int,
    scene_id: int,
    job_id: int,
    payload: dict[str, Any] | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """
    Produce one versioned MP4 clip for a scene via the configured video adapter.

    Default: ffmpeg_kenburns (fallback). AI engines refuse until approved + wired.
    """
    s = settings or get_settings()
    payload = dict(payload or {})
    gates = inspect_video_gates(s)

    scene = await session.get(Scene, scene_id)
    if scene is None or scene.project_id != project_id:
        raise RuntimeError(f"Scene {scene_id} not in project {project_id}")

    engine = str(payload.get("engine") or s.video_engine or "ffmpeg_kenburns").strip().lower()
    duration_sec = float(payload.get("duration_sec", s.video_duration_sec))
    # Hard caps for 6GB / draft clips
    duration_sec = max(0.5, min(duration_sec, float(s.video_max_duration_sec)))
    fps = int(payload.get("fps", s.video_fps))
    width = int(payload.get("width", s.video_width))
    height = int(payload.get("height", s.video_height))

    out_dir = scene_clip_dir(project_id, scene_id, s)
    version = next_clip_version(out_dir)
    filename = f"v{version:03d}.mp4"
    dest = out_dir / filename

    latest_img = await _latest_scene_image(session, scene_id)
    source = resolve_source_still(
        project_id=project_id,
        scene_id=scene_id,
        payload=payload,
        settings=s,
        latest_image_asset=latest_img,
    )

    run_meta: dict[str, Any]
    if engine in AI_VIDEO_ENGINES:
        if source is None:
            raise RuntimeError(
                "AI I2V requires a scene still (generate-image first) or source_image_path"
            )
        try:
            run_meta = await run_comfyui_i2v_stub(
                engine=engine,
                source_image=source,
                dest_mp4=dest,
                settings=s,
                model_filename=payload.get("model"),
            )
        except AIVideoNotApprovedError:
            raise
    elif engine == "mock":
        if source is not None:
            run_meta = await still_to_mp4_kenburns(
                source,
                dest,
                duration_sec=duration_sec,
                fps=fps,
                width=width,
                height=height,
                timeout_sec=s.video_timeout_sec,
            )
            run_meta["engine"] = "mock"
            run_meta["engine_label"] = "fallback_mock_kenburns_not_ai_video"
        else:
            run_meta = await write_minimal_mock_mp4(dest, duration_sec=min(duration_sec, 2.0))
    elif engine in FALLBACK_ENGINES or engine == "ffmpeg_kenburns":
        if source is None:
            raise RuntimeError(
                "ffmpeg_kenburns requires a scene still — run generate-image first "
                "or pass source_image_path. (This fallback is not AI video.)"
            )
        run_meta = await still_to_mp4_kenburns(
            source,
            dest,
            duration_sec=duration_sec,
            fps=fps,
            width=width,
            height=height,
            timeout_sec=s.video_timeout_sec,
        )
    else:
        raise RuntimeError(
            f"Unknown video engine {engine!r}. "
            f"Use one of: ffmpeg_kenburns, mock, comfyui_wan, comfyui_ltx"
        )

    if not dest.is_file():
        raise RuntimeError(f"Clip adapter reported ok but file missing: {dest}")

    rel_path = str(
        Path("projects")
        / str(project_id)
        / "assets"
        / "scenes"
        / str(scene_id)
        / "clips"
        / filename
    )

    ai_video = bool(run_meta.get("ai_video"))
    asset = Asset(
        project_id=project_id,
        scene_id=scene_id,
        character_id=None,
        kind=ASSET_KIND_SCENE_CLIP,
        path=rel_path,
        meta={
            "version": version,
            "absolute_path": str(dest),
            "engine": run_meta.get("engine", engine),
            "engine_label": run_meta.get("engine_label"),
            "ai_video": ai_video,
            "fallback": bool(run_meta.get("fallback", not ai_video)),
            "duration_sec": run_meta.get("duration_sec", duration_sec),
            "fps": run_meta.get("fps", fps),
            "width": run_meta.get("width", width),
            "height": run_meta.get("height", height),
            "frames": run_meta.get("frames"),
            "source_image": run_meta.get("source_image") or (str(source) if source else None),
            "source_image_asset_id": latest_img.id if latest_img else None,
            "job_id": job_id,
            "gate": gates.as_dict(),
            "note": run_meta.get("note"),
        },
    )
    session.add(asset)

    meta = dict(scene.meta or {})
    meta["current_clip_version"] = version
    meta["current_clip_path"] = rel_path
    meta["current_clip_engine"] = run_meta.get("engine", engine)
    meta["current_clip_ai_video"] = ai_video
    scene.meta = meta
    if scene.status in ("draft", "imaged", "scripted"):
        scene.status = "clipped"
    scene.updated_at = utcnow()

    await session.commit()
    await session.refresh(asset)

    logger.info(
        "Scene clip saved project=%s scene=%s version=%s engine=%s ai_video=%s path=%s",
        project_id,
        scene_id,
        version,
        run_meta.get("engine", engine),
        ai_video,
        dest,
    )
    return {
        "ok": True,
        "job_type": "video_generate",
        "asset_id": asset.id,
        "version": version,
        "path": rel_path,
        "absolute_path": str(dest),
        "engine": run_meta.get("engine", engine),
        "ai_video": ai_video,
        "fallback": bool(run_meta.get("fallback", not ai_video)),
        "note": run_meta.get("note")
        or (
            "Clip saved. Prior versions kept. "
            + ("AI video active." if ai_video else "Non-AI fallback — AI I2V not claimed.")
        ),
    }
