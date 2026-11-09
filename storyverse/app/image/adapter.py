"""High-level scene image generation: ComfyUI → versioned project assets.

Regenerating one scene adds a new version file and Asset row; it does NOT
wipe other scenes or earlier versions.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.image.comfyui import ComfyUIClient, ComfyUIError
from app.image.workflow import DEFAULT_CHECKPOINT, build_txt2img_workflow
from app.models import Asset, Character, Scene, utcnow
from app.paths import ensure_project_layout

logger = logging.getLogger("storyverse.image")

ASSET_KIND_SCENE_IMAGE = "scene_image"
ASSET_KIND_CHAR_REF = "character_ref"


def scene_image_dir(project_id: int, scene_id: int, settings: Settings | None = None) -> Path:
    layout = ensure_project_layout(project_id, settings)
    path = layout["assets"] / "scenes" / str(scene_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def character_refs_dir(
    project_id: int, character_id: int, settings: Settings | None = None
) -> Path:
    layout = ensure_project_layout(project_id, settings)
    path = layout["characters"] / str(character_id) / "refs"
    path.mkdir(parents=True, exist_ok=True)
    return path


_VERSION_RE = re.compile(r"^v(\d{3})\.png$", re.IGNORECASE)


def next_image_version(directory: Path) -> int:
    """Scan versioned PNGs (v001.png …) and return the next version number."""
    highest = 0
    if directory.is_dir():
        for p in directory.iterdir():
            m = _VERSION_RE.match(p.name)
            if m:
                highest = max(highest, int(m.group(1)))
    return highest + 1


def compose_positive_prompt(
    scene: Scene,
    *,
    character_snippets: list[str] | None = None,
    extra: str = "",
) -> str:
    """Build a ComfyUI positive prompt from scene fields + optional character stubs."""
    parts: list[str] = []
    if scene.prompt and scene.prompt.strip():
        parts.append(scene.prompt.strip())
    else:
        bits = [scene.title or "cinematic scene"]
        if scene.script_text:
            bits.append(scene.script_text.strip()[:400])
        parts.append(", ".join(bits))
    if scene.camera:
        parts.append(f"camera: {scene.camera.strip()}")
    if scene.lighting:
        parts.append(f"lighting: {scene.lighting.strip()}")
    for snip in character_snippets or []:
        if snip.strip():
            parts.append(snip.strip())
    if extra.strip():
        parts.append(extra.strip())
    parts.append("cinematic still, highly detailed, film still")
    return ", ".join(parts)


async def _character_snippets(
    session: AsyncSession, project_id: int, character_ids: list[int] | None
) -> list[str]:
    if not character_ids:
        return []
    result = await session.execute(
        select(Character).where(
            Character.project_id == project_id,
            Character.id.in_(character_ids),
        )
    )
    chars = list(result.scalars())
    snippets: list[str] = []
    for c in chars:
        meta = c.meta or {}
        visual = str(meta.get("visual_prompt") or meta.get("reference_notes") or "").strip()
        desc = (c.description or "").strip()
        if visual:
            snippets.append(f"character {c.name}: {visual}")
        elif desc:
            snippets.append(f"character {c.name}: {desc[:240]}")
        else:
            snippets.append(f"character {c.name}")
    return snippets


async def count_scene_image_versions(session: AsyncSession, scene_id: int) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(Asset)
        .where(Asset.scene_id == scene_id, Asset.kind == ASSET_KIND_SCENE_IMAGE)
    )
    return int(result.scalar_one() or 0)


async def generate_scene_image(
    session: AsyncSession,
    *,
    project_id: int,
    scene_id: int,
    job_id: int,
    payload: dict[str, Any] | None = None,
    settings: Settings | None = None,
    client: ComfyUIClient | None = None,
) -> dict[str, Any]:
    """
    Run ComfyUI for one scene, copy PNG into versioned assets/, insert Asset row.

    Does not delete prior versions or other scenes' assets.
    """
    s = settings or get_settings()
    payload = dict(payload or {})

    scene = await session.get(Scene, scene_id)
    if scene is None or scene.project_id != project_id:
        raise ComfyUIError(f"Scene {scene_id} not in project {project_id}")

    character_ids = payload.get("character_ids")
    if character_ids is not None and not isinstance(character_ids, list):
        character_ids = None
    snippets = await _character_snippets(session, project_id, character_ids)

    positive = payload.get("prompt_override") or compose_positive_prompt(
        scene,
        character_snippets=snippets,
        extra=str(payload.get("extra_prompt") or ""),
    )
    negative = payload.get("negative_prompt")
    checkpoint = str(payload.get("checkpoint") or s.comfyui_checkpoint or DEFAULT_CHECKPOINT)
    # Never allow empty / remote download hints — stick to local filename only
    if "/" in checkpoint or "\\" in checkpoint or checkpoint.startswith("http"):
        raise ComfyUIError(
            "checkpoint must be a local ComfyUI filename "
            f"(expected {DEFAULT_CHECKPOINT}), got {checkpoint!r}"
        )

    seed = int(payload.get("seed", 42 + scene_id * 17 + job_id))
    steps = int(payload.get("steps", s.comfyui_steps))
    cfg = float(payload.get("cfg", s.comfyui_cfg))
    width = int(payload.get("width", s.comfyui_width))
    height = int(payload.get("height", s.comfyui_height))

    out_dir = scene_image_dir(project_id, scene_id, s)
    version = next_image_version(out_dir)
    filename = f"v{version:03d}.png"
    dest = out_dir / filename
    prefix = f"StoryVerse_p{project_id}_s{scene_id}_j{job_id}"

    workflow = build_txt2img_workflow(
        positive=positive,
        negative=negative if isinstance(negative, str) else None,
        checkpoint=checkpoint,
        seed=seed,
        steps=steps,
        cfg=cfg,
        width=width,
        height=height,
        filename_prefix=prefix,
    )

    comfy = client or ComfyUIClient(
        s.comfyui_base_url,
        timeout_sec=s.comfyui_timeout_sec,
        poll_interval_sec=s.comfyui_poll_interval_sec,
    )
    prompt_id, image_bytes, ref = await comfy.run_workflow(workflow)

    dest.write_bytes(image_bytes)
    rel_path = str(Path("projects") / str(project_id) / "assets" / "scenes" / str(scene_id) / filename)

    asset = Asset(
        project_id=project_id,
        scene_id=scene_id,
        character_id=None,
        kind=ASSET_KIND_SCENE_IMAGE,
        path=rel_path,
        meta={
            "version": version,
            "absolute_path": str(dest),
            "prompt": positive,
            "negative_prompt": negative if isinstance(negative, str) else None,
            "seed": seed,
            "steps": steps,
            "cfg": cfg,
            "width": width,
            "height": height,
            "checkpoint": checkpoint,
            "comfy_prompt_id": prompt_id,
            "comfy_filename": ref.get("filename"),
            "job_id": job_id,
            "character_ids": character_ids or [],
        },
    )
    session.add(asset)

    # Point scene at latest version without removing prior assets
    meta = dict(scene.meta or {})
    meta["current_image_version"] = version
    meta["current_image_path"] = rel_path
    scene.meta = meta
    scene.status = "imaged"
    scene.updated_at = utcnow()

    await session.commit()
    await session.refresh(asset)

    logger.info(
        "Scene image saved project=%s scene=%s version=%s path=%s",
        project_id,
        scene_id,
        version,
        dest,
    )
    return {
        "ok": True,
        "job_type": "image_generate",
        "asset_id": asset.id,
        "version": version,
        "path": rel_path,
        "absolute_path": str(dest),
        "comfy_prompt_id": prompt_id,
        "checkpoint": checkpoint,
        "seed": seed,
        "note": "Copied ComfyUI output into project assets (prior versions kept)",
    }


def ensure_character_ref_stub(
    project_id: int,
    character_id: int,
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """
    Light character-reference stub: create refs/ folder + README placeholder.
    Does not generate images or download models.
    """
    refs = character_refs_dir(project_id, character_id, settings)
    readme = refs / "README.txt"
    if not readme.exists():
        readme.write_text(
            "Place optional reference images for this character here.\n"
            "Phase 5 uses description / visual_prompt in character.meta for prompt hints only.\n"
            "No IP-Adapter / LoRA is wired by default (VRAM / complexity).\n",
            encoding="utf-8",
        )
    return {
        "refs_dir": str(refs),
        "readme": str(readme),
        "stub": True,
    }
