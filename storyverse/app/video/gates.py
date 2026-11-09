"""Gates for AI video models — OFF by default; never auto-download weights.

Honesty policy (Phase 6):
  - FFmpeg Ken Burns / still→MP4 is a **fallback**, not AI I2V.
  - ComfyUI Wan / LTX adapters stay disabled until the user sets
    STORYVERSE_ALLOW_AI_VIDEO=1 **and** local model files already exist.
  - STORYVERSE_ALLOW_VIDEO_MODEL_DOWNLOAD=1 only documents user approval to
    *manually* fetch weights later — this codebase never downloads them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import Settings, get_settings

# Engines that claim AI I2V (require allow_ai_video + on-disk models)
AI_VIDEO_ENGINES = frozenset({"comfyui_wan", "comfyui_ltx"})

# Engines that are honest non-AI fallbacks / mocks (smoke-safe)
FALLBACK_ENGINES = frozenset({"ffmpeg_kenburns", "mock"})

KNOWN_ENGINES = AI_VIDEO_ENGINES | FALLBACK_ENGINES


@dataclass(frozen=True)
class VideoGateStatus:
    engine: str
    allow_ai_video: bool
    allow_video_model_download: bool
    ai_video_active: bool
    is_fallback: bool
    notes: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "engine": self.engine,
            "allow_ai_video": self.allow_ai_video,
            "allow_video_model_download": self.allow_video_model_download,
            "ai_video_active": self.ai_video_active,
            "is_fallback": self.is_fallback,
            "notes": list(self.notes),
        }


def inspect_video_gates(settings: Settings | None = None) -> VideoGateStatus:
    s = settings or get_settings()
    engine = (s.video_engine or "ffmpeg_kenburns").strip().lower()
    notes: list[str] = []

    if engine not in KNOWN_ENGINES:
        notes.append(
            f"Unknown video_engine={engine!r}; known: {', '.join(sorted(KNOWN_ENGINES))}"
        )

    is_fallback = engine in FALLBACK_ENGINES
    ai_requested = engine in AI_VIDEO_ENGINES
    ai_active = bool(ai_requested and s.allow_ai_video)

    if is_fallback:
        notes.append(
            "Active path is a labeled non-AI fallback (Ken Burns / mock still→MP4). "
            "Do not claim AI video generation."
        )
    if ai_requested and not s.allow_ai_video:
        notes.append(
            "AI I2V engine selected but STORYVERSE_ALLOW_AI_VIDEO is OFF. "
            "Jobs will refuse AI path until explicit approval + local models."
        )
    if s.allow_ai_video and not ai_requested:
        notes.append(
            "STORYVERSE_ALLOW_AI_VIDEO=1 but video_engine is still a fallback. "
            "Set STORYVERSE_VIDEO_ENGINE=comfyui_wan|comfyui_ltx only after models exist."
        )
    if s.allow_video_model_download:
        notes.append(
            "STORYVERSE_ALLOW_VIDEO_MODEL_DOWNLOAD=1 records user approval for a "
            "*manual* future download — StoryVerse never auto-downloads video weights."
        )
    else:
        notes.append(
            "Video model download gate OFF. Large Wan/LTX downloads need explicit "
            "user approval (set STORYVERSE_ALLOW_VIDEO_MODEL_DOWNLOAD=1) + README steps."
        )

    # RTX 4050 6GB reminder always present for AI path docs
    notes.append(
        "RTX 4050 6GB: prefer quantized/GGUF Wan 1.3B or LTX 2B distilled; "
        "short clips, low res/frames; expect minutes per clip; OOM risk if unconstrained."
    )

    return VideoGateStatus(
        engine=engine,
        allow_ai_video=bool(s.allow_ai_video),
        allow_video_model_download=bool(s.allow_video_model_download),
        ai_video_active=ai_active,
        is_fallback=is_fallback or not ai_active,
        notes=notes,
    )


def assert_no_download_urls(value: str, *, field: str = "model") -> None:
    """Reject remote URLs / path tricks that look like download instructions."""
    v = (value or "").strip()
    if not v:
        return
    lowered = v.lower()
    if lowered.startswith(("http://", "https://", "ftp://", "s3://", "hf://")):
        raise RuntimeError(
            f"{field} must be a local filename/path already on disk; "
            f"got remote URL {value!r}. No automatic downloads."
        )
    if "huggingface.co" in lowered or "hf-mirror" in lowered:
        raise RuntimeError(
            f"{field} looks like a Hub download reference ({value!r}). "
            "Install models manually after explicit approval; see README."
        )
