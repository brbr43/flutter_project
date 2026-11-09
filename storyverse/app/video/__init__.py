"""Phase 6 — short clip video engine (adapters + versioned scene clips).

Default path is a labeled FFmpeg Ken Burns / still→MP4 **fallback**, not AI video.
Wan 1.3B / LTX via ComfyUI are adapter stubs gated behind explicit approval flags.
NO automatic model downloads.
"""

from app.video.adapter import (
    ASSET_KIND_SCENE_CLIP,
    generate_scene_clip,
    scene_clip_dir,
)

__all__ = [
    "ASSET_KIND_SCENE_CLIP",
    "generate_scene_clip",
    "scene_clip_dir",
]
