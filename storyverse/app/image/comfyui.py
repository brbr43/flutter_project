"""ComfyUI HTTP client — talks to a local server (default 127.0.0.1:8188).

No model downloads. The checkpoint must already be installed in ComfyUI.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Optional

import httpx

logger = logging.getLogger("storyverse.comfyui")


class ComfyUIError(RuntimeError):
    """Raised when ComfyUI is unreachable or a prompt fails."""


class ComfyUIClient:
    """Thin async wrapper around ComfyUI's HTTP API."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8188",
        *,
        timeout_sec: float = 300.0,
        poll_interval_sec: float = 0.5,
        client_id: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = float(timeout_sec)
        self.poll_interval_sec = float(poll_interval_sec)
        self.client_id = client_id or str(uuid.uuid4())
        self._transport = transport

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(30.0, read=self.timeout_sec),
            transport=self._transport,
        )

    async def health(self) -> dict[str, Any]:
        """Lightweight reachability check (system_stats or root)."""
        async with self._client() as client:
            try:
                r = await client.get("/system_stats")
                if r.status_code == 200:
                    return {"ok": True, "endpoint": "system_stats", "data": r.json()}
            except httpx.HTTPError as exc:
                raise ComfyUIError(f"ComfyUI unreachable at {self.base_url}: {exc}") from exc
            # Some builds expose /object_info instead
            try:
                r = await client.get("/object_info")
                if r.status_code == 200:
                    return {"ok": True, "endpoint": "object_info", "keys": len(r.json())}
            except httpx.HTTPError as exc:
                raise ComfyUIError(f"ComfyUI unreachable at {self.base_url}: {exc}") from exc
            raise ComfyUIError(
                f"ComfyUI at {self.base_url} responded HTTP {r.status_code} "
                "(is ComfyUI running on Windows?)"
            )

    async def queue_prompt(self, workflow: dict[str, Any]) -> str:
        """POST /prompt — returns prompt_id."""
        body = {"prompt": workflow, "client_id": self.client_id}
        async with self._client() as client:
            try:
                r = await client.post("/prompt", json=body)
            except httpx.HTTPError as exc:
                raise ComfyUIError(f"Failed to POST /prompt: {exc}") from exc
            if r.status_code >= 400:
                raise ComfyUIError(f"/prompt HTTP {r.status_code}: {r.text[:500]}")
            data = r.json()
            if "error" in data:
                raise ComfyUIError(f"/prompt error: {data['error']}")
            prompt_id = data.get("prompt_id")
            if not prompt_id:
                raise ComfyUIError(f"/prompt missing prompt_id: {data}")
            logger.info("ComfyUI queued prompt_id=%s", prompt_id)
            return str(prompt_id)

    async def get_history(self, prompt_id: str) -> Optional[dict[str, Any]]:
        async with self._client() as client:
            try:
                r = await client.get(f"/history/{prompt_id}")
            except httpx.HTTPError as exc:
                raise ComfyUIError(f"Failed to GET /history: {exc}") from exc
            if r.status_code == 404:
                return None
            if r.status_code >= 400:
                raise ComfyUIError(f"/history HTTP {r.status_code}: {r.text[:500]}")
            data = r.json()
            if not data:
                return None
            # Response is {prompt_id: {...}} or already the entry
            if prompt_id in data:
                return data[prompt_id]
            return data

    async def wait_for_prompt(self, prompt_id: str) -> dict[str, Any]:
        """Poll /history until outputs appear or timeout."""
        deadline = asyncio.get_event_loop().time() + self.timeout_sec
        while True:
            entry = await self.get_history(prompt_id)
            if entry and entry.get("outputs"):
                return entry
            if entry and entry.get("status", {}).get("status_str") == "error":
                raise ComfyUIError(f"ComfyUI prompt failed: {entry.get('status')}")
            if asyncio.get_event_loop().time() >= deadline:
                raise ComfyUIError(
                    f"Timed out after {self.timeout_sec}s waiting for prompt_id={prompt_id}"
                )
            await asyncio.sleep(self.poll_interval_sec)

    @staticmethod
    def extract_image_refs(history_entry: dict[str, Any]) -> list[dict[str, str]]:
        """Collect SaveImage outputs from a history entry."""
        refs: list[dict[str, str]] = []
        outputs = history_entry.get("outputs") or {}
        for _node_id, node_out in outputs.items():
            for img in node_out.get("images") or []:
                refs.append(
                    {
                        "filename": str(img.get("filename") or ""),
                        "subfolder": str(img.get("subfolder") or ""),
                        "type": str(img.get("type") or "output"),
                    }
                )
        return [r for r in refs if r["filename"]]

    async def download_image(
        self,
        *,
        filename: str,
        subfolder: str = "",
        image_type: str = "output",
    ) -> bytes:
        params = {"filename": filename, "subfolder": subfolder, "type": image_type}
        async with self._client() as client:
            try:
                r = await client.get("/view", params=params)
            except httpx.HTTPError as exc:
                raise ComfyUIError(f"Failed to GET /view: {exc}") from exc
            if r.status_code >= 400:
                raise ComfyUIError(f"/view HTTP {r.status_code}: {r.text[:200]}")
            return r.content

    async def run_workflow(self, workflow: dict[str, Any]) -> tuple[str, bytes, dict[str, str]]:
        """Queue → wait → download first output image. Returns (prompt_id, bytes, ref)."""
        prompt_id = await self.queue_prompt(workflow)
        entry = await self.wait_for_prompt(prompt_id)
        refs = self.extract_image_refs(entry)
        if not refs:
            raise ComfyUIError(f"No image outputs for prompt_id={prompt_id}")
        ref = refs[0]
        data = await self.download_image(
            filename=ref["filename"],
            subfolder=ref["subfolder"],
            image_type=ref["type"],
        )
        if not data:
            raise ComfyUIError(f"Empty image download for {ref}")
        return prompt_id, data, ref
