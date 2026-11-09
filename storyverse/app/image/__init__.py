"""Phase 5 — ComfyUI image generation adapter (DreamShaper; no model downloads)."""

from app.image.adapter import generate_scene_image, next_image_version, scene_image_dir
from app.image.comfyui import ComfyUIClient, ComfyUIError

__all__ = [
    "ComfyUIClient",
    "ComfyUIError",
    "generate_scene_image",
    "next_image_version",
    "scene_image_dir",
]
