"""Optional LLM adapters — OFF by default. No model downloads. No paid APIs unless gated.

Local LLM: requires STORYVERSE_ALLOW_LOCAL_LLM=1 (still not implemented beyond gate —
Phase 4 ships template generator as the working path).

Cloud LLM: requires STORYVERSE_ALLOW_CLOUD_LLM=1 AND a non-empty API key
(STORYVERSE_CLOUD_LLM_API_KEY). Even then this module only documents the gate;
generation stays template-based unless a future phase wires a real client.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

from app.config import Settings, get_settings

logger = logging.getLogger("storyverse.story.llm")


@dataclass(frozen=True)
class LLMGateStatus:
    local_allowed: bool
    cloud_allowed: bool
    cloud_key_present: bool
    active_backend: str  # "template" | "local_llm" | "cloud_llm"
    notes: str


def inspect_llm_gates(settings: Settings | None = None) -> LLMGateStatus:
    s = settings or get_settings()
    local_ok = bool(s.allow_local_llm)
    cloud_flag = bool(s.allow_cloud_llm)
    key = (s.cloud_llm_api_key or "").strip()
    cloud_key = bool(key)
    cloud_ok = cloud_flag and cloud_key

    if cloud_ok:
        backend = "cloud_llm"
        notes = (
            "Cloud LLM gate OPEN (STORYVERSE_ALLOW_CLOUD_LLM=1 + key). "
            "Phase 4 still uses the template generator; cloud calls are not auto-invoked."
        )
    elif local_ok:
        backend = "local_llm"
        notes = (
            "Local LLM gate OPEN (STORYVERSE_ALLOW_LOCAL_LLM=1). "
            "No model download or local inference is performed in Phase 4 — template path used."
        )
    else:
        backend = "template"
        notes = (
            "Default: deterministic templates. "
            "Local LLM off. Cloud LLM off or missing key."
        )

    if cloud_flag and not cloud_key:
        notes += " STORYVERSE_ALLOW_CLOUD_LLM=1 but STORYVERSE_CLOUD_LLM_API_KEY is empty — cloud blocked."

    return LLMGateStatus(
        local_allowed=local_ok,
        cloud_allowed=cloud_ok,
        cloud_key_present=cloud_key,
        active_backend=backend if backend == "template" else "template",  # Phase 4: always template
        notes=notes,
    )


def try_cloud_complete(_prompt: str, *, settings: Settings | None = None) -> Optional[dict[str, Any]]:
    """Gated stub — refuses unless flag+key; never downloads models; never calls paid APIs in Phase 4."""
    status = inspect_llm_gates(settings)
    if not status.cloud_allowed:
        logger.info("Cloud LLM refused: %s", status.notes)
        return None
    # Explicitly do NOT call any remote API in Phase 4 — document-only gate.
    logger.warning(
        "Cloud LLM gate is open but Phase 4 does not invoke paid APIs; "
        "returning None so caller falls back to templates."
    )
    return None


def try_local_complete(_prompt: str, *, settings: Settings | None = None) -> Optional[dict[str, Any]]:
    """Gated stub — local LLM off by default; never downloads weights."""
    status = inspect_llm_gates(settings)
    if not status.local_allowed:
        logger.info("Local LLM refused (flag off).")
        return None
    logger.warning(
        "Local LLM flag is on but Phase 4 does not load models; "
        "returning None so caller falls back to templates."
    )
    return None
