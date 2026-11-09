"""ComfyUI I2V adapters for Wan 1.3B / LTX — stubs until models are approved.

Phase 6 ships the adapter surface so Wan/LTX can plug in later without API churn.
These paths:
  - NEVER download weights
  - Refuse unless STORYVERSE_ALLOW_AI_VIDEO=1
  - Refuse unless a local model file path is already present
  - Document RTX 4050 6GB limits in errors / README
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.config import Settings, get_settings
from app.video.gates import assert_no_download_urls

logger = logging.getLogger("storyverse.video.comfyui_i2v")

# Expected *local* filenames once the user installs after approval (not fetched here).
WAN_DEFAULT_MODEL = "wan2.1_t2v_1.3B_fp8.safetensors"
LTX_DEFAULT_MODEL = "ltx-video-2b-v0.9.distilled.safetensors"


class AIVideoNotApprovedError(RuntimeError):
    """Raised when AI I2V is requested without gates / local models."""


def _model_search_dirs(settings: Settings) -> list[Path]:
    """Places to look for already-installed video weights (Windows D: layout + Comfy)."""
    root = settings.root
    return [
        root / "models" / "checkpoints",
        root / "models" / "diffusion_models",
        root / "models" / "unet",
        root / "apps" / "comfyui" / "models" / "checkpoints",
        root / "apps" / "comfyui" / "models" / "diffusion_models",
        root / "apps" / "comfyui" / "models" / "unet",
    ]


def find_local_model(filename: str, settings: Settings | None = None) -> Path | None:
    s = settings or get_settings()
    assert_no_download_urls(filename, field="video_model")
    name = Path(filename).name  # strip any path components
    for folder in _model_search_dirs(s):
        candidate = folder / name
        if candidate.is_file():
            return candidate
    return None


def require_ai_video_ready(
    engine: str,
    *,
    settings: Settings | None = None,
    model_filename: str | None = None,
) -> Path:
    """
    Validate gates + on-disk model. Does not download. Does not call ComfyUI yet.

    Returns the resolved local model Path when ready (future workflow wiring).
    """
    s = settings or get_settings()
    engine = engine.strip().lower()

    if not s.allow_ai_video:
        raise AIVideoNotApprovedError(
            "AI video is OFF. Set STORYVERSE_ALLOW_AI_VIDEO=1 only after you "
            "explicitly approve using Wan/LTX on this machine. "
            "Default Phase 6 path remains ffmpeg_kenburns (non-AI fallback). "
            "See storyverse/README.md § Phase 6 video models."
        )

    if engine == "comfyui_wan":
        model = model_filename or s.video_wan_model or WAN_DEFAULT_MODEL
    elif engine == "comfyui_ltx":
        model = model_filename or s.video_ltx_model or LTX_DEFAULT_MODEL
    else:
        raise AIVideoNotApprovedError(f"Unsupported AI video engine: {engine!r}")

    assert_no_download_urls(model, field="video_model")
    found = find_local_model(model, s)
    if found is None:
        download_hint = (
            "STORYVERSE_ALLOW_VIDEO_MODEL_DOWNLOAD is ON — you may *manually* "
            "download the approved weights into D:\\StoryVerse\\models\\… "
            "(StoryVerse will not fetch them)."
            if s.allow_video_model_download
            else (
                "Download gate is OFF. To approve a future *manual* install, set "
                "STORYVERSE_ALLOW_VIDEO_MODEL_DOWNLOAD=1 and follow README VRAM notes "
                "for RTX 4050 6GB (quantized Wan 1.3B or LTX 2B distilled)."
            )
        )
        raise AIVideoNotApprovedError(
            f"AI I2V engine={engine} approved via flag, but local model "
            f"{model!r} was not found under {s.root}/models or ComfyUI models. "
            f"{download_hint} "
            "Do not claim AI video works until the file exists and a live ComfyUI "
            "I2V run succeeds."
        )

    logger.info("AI video model present for %s: %s (ComfyUI workflow not wired in Phase 6 stub)", engine, found)
    # Phase 6 honesty: even with file present we do not run an unverified I2V graph.
    raise AIVideoNotApprovedError(
        f"Local model found at {found}, and STORYVERSE_ALLOW_AI_VIDEO=1, but the "
        f"ComfyUI {engine} I2V workflow is not enabled in this Phase 6 build "
        "(adapter stub only). Keep using video_engine=ffmpeg_kenburns until a "
        "follow-up wires + validates low-VRAM Wan/LTX graphs on RTX 4050 6GB. "
        "AI video is therefore still NOT claimed working."
    )


async def run_comfyui_i2v_stub(
    *,
    engine: str,
    source_image: Path,
    dest_mp4: Path,
    settings: Settings | None = None,
    model_filename: str | None = None,
) -> dict[str, Any]:
    """Entry used by the high-level adapter — always raises until workflow lands."""
    require_ai_video_ready(engine, settings=settings, model_filename=model_filename)
    # Unreachable until require_ai_video_ready starts returning for a wired path
    return {
        "ok": False,
        "engine": engine,
        "ai_video": False,
        "source_image": str(source_image),
        "path": str(dest_mp4),
    }
