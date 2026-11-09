"""ComfyUI API workflow graphs for StoryVerse image generation.

Default checkpoint: DreamShaper_8_pruned.safetensors (already on the user's
Windows machine from Phase 2). This module NEVER downloads models.
"""

from __future__ import annotations

from typing import Any


# Fixed filename — must already exist under ComfyUI models/checkpoints/
DEFAULT_CHECKPOINT = "DreamShaper_8_pruned.safetensors"

DEFAULT_NEGATIVE = (
    "lowres, blurry, deformed, bad anatomy, watermark, text, logo, "
    "extra limbs, poorly drawn, jpeg artifacts"
)


def build_txt2img_workflow(
    *,
    positive: str,
    negative: str | None = None,
    checkpoint: str = DEFAULT_CHECKPOINT,
    seed: int = 42,
    steps: int = 20,
    cfg: float = 7.0,
    width: int = 512,
    height: int = 512,
    filename_prefix: str = "StoryVerse",
) -> dict[str, Any]:
    """
    Minimal SD1.5 txt2img graph (CheckpointLoader → CLIP/VAE → KSampler → SaveImage).

    Node ids are strings as required by the ComfyUI `/prompt` API.
    """
    neg = negative if negative is not None else DEFAULT_NEGATIVE
    # Cap for 6GB VRAM policy (Phase 1): 512–768, batch=1
    width = max(256, min(int(width), 768))
    height = max(256, min(int(height), 768))
    steps = max(1, min(int(steps), 40))
    cfg = max(1.0, min(float(cfg), 15.0))

    return {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": int(seed) & 0xFFFFFFFFFFFFFFFF,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": checkpoint,
            },
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1,
            },
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": positive,
                "clip": ["4", 1],
            },
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": neg,
                "clip": ["4", 1],
            },
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["3", 0],
                "vae": ["4", 2],
            },
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": filename_prefix,
                "images": ["8", 0],
            },
        },
    }
