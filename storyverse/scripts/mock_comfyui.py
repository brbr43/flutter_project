"""Minimal fake ComfyUI HTTP server for CI / cloud smoke tests (no GPU).

Implements the subset used by StoryVerse:
  GET  /system_stats
  POST /prompt
  GET  /history/{prompt_id}
  GET  /view

Usage:
  python scripts/mock_comfyui.py --port 18188
"""

from __future__ import annotations

import argparse
import struct
import uuid
import zlib
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response

# 1x1 PNG (valid) — enough for asset copy / smoke
def _tiny_png(width: int = 8, height: int = 8, rgb: tuple[int, int, int] = (40, 90, 160)) -> bytes:
    """Build a tiny solid-color PNG without Pillow."""

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = b""
    r, g, b = rgb
    row = b"\x00" + bytes([r, g, b]) * width
    raw = row * height
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


TINY_PNG = _tiny_png()


def create_mock_app() -> FastAPI:
    app = FastAPI(title="Mock ComfyUI", version="0.0.1")
    store: dict[str, dict[str, Any]] = {}

    @app.get("/system_stats")
    async def system_stats() -> dict[str, Any]:
        return {
            "system": {"os": "mock", "comfyui_version": "mock-0.0.1"},
            "devices": [{"name": "MockGPU", "type": "cpu", "vram_total": 0}],
        }

    @app.get("/object_info")
    async def object_info() -> dict[str, Any]:
        return {"CheckpointLoaderSimple": {"input": {"required": {"ckpt_name": [["DreamShaper_8_pruned.safetensors"]]}}}}

    @app.post("/prompt")
    async def prompt(body: dict[str, Any]) -> dict[str, Any]:
        wf = body.get("prompt")
        if not isinstance(wf, dict) or not wf:
            raise HTTPException(status_code=400, detail="prompt workflow required")
        # Validate checkpoint name is present (no download)
        ckpt_node = wf.get("4") or {}
        ckpt = (ckpt_node.get("inputs") or {}).get("ckpt_name", "")
        if not ckpt:
            raise HTTPException(status_code=400, detail="missing ckpt_name")
        prompt_id = str(uuid.uuid4())
        prefix = ((wf.get("9") or {}).get("inputs") or {}).get("filename_prefix") or "StoryVerse"
        filename = f"{prefix}_00001_.png"
        store[prompt_id] = {
            "filename": filename,
            "subfolder": "",
            "type": "output",
            "checkpoint": ckpt,
        }
        return {"prompt_id": prompt_id, "number": len(store)}

    @app.get("/history/{prompt_id}")
    async def history(prompt_id: str) -> dict[str, Any]:
        entry = store.get(prompt_id)
        if entry is None:
            return {}
        return {
            prompt_id: {
                "prompt": [],
                "outputs": {
                    "9": {
                        "images": [
                            {
                                "filename": entry["filename"],
                                "subfolder": entry["subfolder"],
                                "type": entry["type"],
                            }
                        ]
                    }
                },
                "status": {"status_str": "success", "completed": True},
            }
        }

    @app.get("/view")
    async def view(
        filename: str = Query(...),
        subfolder: str = Query(""),
        type: str = Query("output"),  # noqa: A002 — ComfyUI query name
    ) -> Response:
        # Any known or unknown filename returns a tiny PNG (smoke only)
        _ = (filename, subfolder, type)
        return Response(content=TINY_PNG, media_type="image/png")

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Mock ComfyUI for StoryVerse smoke tests")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18188)
    args = parser.parse_args()
    import uvicorn

    uvicorn.run(create_mock_app(), host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
