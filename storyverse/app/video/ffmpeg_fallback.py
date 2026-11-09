"""FFmpeg still→MP4 Ken Burns fallback — labeled non-AI.

Used for smoke tests and as the default Phase 6 clip path until the user
approves AI video models (Wan / LTX) and installs them locally.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger("storyverse.video.ffmpeg")

ENGINE_ID = "ffmpeg_kenburns"
ENGINE_LABEL = "fallback_ffmpeg_kenburns_not_ai_video"


class FFmpegFallbackError(RuntimeError):
    pass


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


async def still_to_mp4_kenburns(
    source_image: Path,
    dest_mp4: Path,
    *,
    duration_sec: float = 3.0,
    fps: int = 12,
    width: int = 512,
    height: int = 512,
    timeout_sec: float = 120.0,
) -> dict[str, Any]:
    """
    Animate a still into a short MP4 via zoompan (Ken Burns style).

    This is **not** AI image-to-video. Meta must always carry engine=ffmpeg_kenburns
    and ai_video=False.
    """
    if not source_image.is_file():
        raise FFmpegFallbackError(f"Source still not found: {source_image}")
    if not ffmpeg_available():
        raise FFmpegFallbackError(
            "ffmpeg not found on PATH. Install FFmpeg for the Ken Burns fallback."
        )

    duration_sec = max(0.5, float(duration_sec))
    fps = max(1, min(int(fps), 30))
    width = max(64, min(int(width), 1280))
    height = max(64, min(int(height), 1280))
    # Even dimensions required by yuv420p / libx264
    width -= width % 2
    height -= height % 2
    frames = max(1, int(round(duration_sec * fps)))

    # Gentle zoom: start at 1.0, end ~1.12 over `frames` output frames
    # zoompan d=frames; force output size + fps
    z_end = 1.12
    z_step = (z_end - 1.0) / max(frames, 1)
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"zoompan=z='min(zoom+{z_step:.6f},{z_end})'"
        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        f":d=1:s={width}x{height}:fps={fps},"
        f"trim=end_frame={frames},setpts=PTS-STARTPTS"
    )

    dest_mp4.parent.mkdir(parents=True, exist_ok=True)
    if dest_mp4.exists():
        dest_mp4.unlink()

    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-loop",
        "1",
        "-i",
        str(source_image),
        "-vf",
        vf,
        "-frames:v",
        str(frames),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(dest_mp4),
    ]

    logger.info("FFmpeg Ken Burns fallback: %s → %s (%ss @ %sfps)", source_image, dest_mp4, duration_sec, fps)
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
    except asyncio.TimeoutError as exc:
        proc.kill()
        await proc.wait()
        raise FFmpegFallbackError(f"ffmpeg timed out after {timeout_sec}s") from exc

    if proc.returncode != 0 or not dest_mp4.is_file() or dest_mp4.stat().st_size < 32:
        err = (stderr or b"").decode("utf-8", errors="replace")[:800]
        raise FFmpegFallbackError(f"ffmpeg failed (code={proc.returncode}): {err}")

    return {
        "ok": True,
        "engine": ENGINE_ID,
        "engine_label": ENGINE_LABEL,
        "ai_video": False,
        "fallback": True,
        "source_image": str(source_image),
        "path": str(dest_mp4),
        "duration_sec": duration_sec,
        "fps": fps,
        "width": width,
        "height": height,
        "frames": frames,
        "note": (
            "FFmpeg Ken Burns still→MP4 fallback — NOT AI image-to-video. "
            "Wan/LTX require separate model approval."
        ),
    }


async def write_minimal_mock_mp4(dest_mp4: Path, *, duration_sec: float = 1.0) -> dict[str, Any]:
    """
    Tiny synthetic MP4 via ffmpeg lavfi (no source still).

    Used only when engine=mock and no still is available — still labeled non-AI.
    """
    if not ffmpeg_available():
        raise FFmpegFallbackError("ffmpeg not found on PATH (needed for mock clip)")

    dest_mp4.parent.mkdir(parents=True, exist_ok=True)
    duration_sec = max(0.5, float(duration_sec))
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        f"color=c=gray:s=320x240:d={duration_sec}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(dest_mp4),
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0 or not dest_mp4.is_file():
        err = (stderr or b"").decode("utf-8", errors="replace")[:500]
        raise FFmpegFallbackError(f"mock ffmpeg failed: {err}")
    return {
        "ok": True,
        "engine": "mock",
        "engine_label": "fallback_mock_lavfi_not_ai_video",
        "ai_video": False,
        "fallback": True,
        "path": str(dest_mp4),
        "duration_sec": duration_sec,
        "note": "Mock lavfi MP4 — NOT AI video.",
    }
