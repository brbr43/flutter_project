"""Deterministic template-based story / script / scene generator.

Produces editable JSON: title, synopsis, beats, scenes
(with camera / lighting / prompts / content_tag). No ML.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from app.story.llm import inspect_llm_gates, try_cloud_complete, try_local_complete
from app.story.templates import CONTENT_TAGS, GENRE_IDS, genre_catalog, get_genre


def list_genres() -> list[dict[str, Any]]:
    return genre_catalog()


def _slug_words(idea: str, limit: int = 8) -> str:
    words = re.findall(r"[\w\u0600-\u06FF]+", idea.strip(), flags=re.UNICODE)
    if not words:
        return "Untitled Story"
    return " ".join(words[:limit])


def _stable_seed(idea: str, genre: str) -> str:
    h = hashlib.sha256(f"{genre}|{idea.strip().lower()}".encode("utf-8")).hexdigest()
    return h[:12]


def _title_from_idea(idea: str, genre_label: str) -> str:
    core = _slug_words(idea, 6)
    if len(core) > 80:
        core = core[:77] + "..."
    return f"{core} ({genre_label})"


def _synopsis(idea: str, genre: dict[str, Any], true_story: bool) -> str:
    mode = (
        "True-story mode: scenes are tagged fact vs dramatization."
        if true_story
        else "Fictional dramatic mode."
    )
    return (
        f"{idea.strip()}\n\n"
        f"Genre tone: {genre['tone']}. {mode} "
        f"Draft produced by StoryVerse Phase 4 template generator "
        f"(editable; not a cinematic final)."
    )


def _apply_true_story_tags(tag: str, true_story: bool) -> str:
    if not true_story:
        # Keep fiction for fiction genres; allow fact/dramatization only when true_story
        if tag in ("fact", "dramatization"):
            return "fiction"
        return tag if tag in CONTENT_TAGS else "fiction"
    # true-story: preserve fact/dramatization from blueprint; map fiction → dramatization
    if tag == "fiction":
        return "dramatization"
    return tag if tag in CONTENT_TAGS else "fact"


def generate_story_draft(
    idea: str,
    genre: str = "drama",
    *,
    true_story_mode: bool = False,
    preferred_backend: str = "auto",
    language: str = "en",
) -> dict[str, Any]:
    """
    Build a full editable story draft dict.

    preferred_backend: "auto" | "template" | "local_llm" | "cloud_llm"
    Phase 4 always returns template output; LLM backends are gated stubs that fall back.
    """
    idea_clean = (idea or "").strip()
    if not idea_clean:
        raise ValueError("idea must be non-empty")

    g = get_genre(genre)
    gate = inspect_llm_gates()
    used_backend = "template"
    backend_notes = gate.notes

    # Attempt optional backends only if explicitly requested / auto with flags — still fall back.
    if preferred_backend in ("cloud_llm", "auto") and gate.cloud_allowed:
        cloud = try_cloud_complete(idea_clean)
        if cloud is not None:
            used_backend = "cloud_llm"
    elif preferred_backend == "local_llm" or (
        preferred_backend == "auto" and gate.local_allowed and not gate.cloud_allowed
    ):
        local = try_local_complete(idea_clean)
        if local is not None:
            used_backend = "local_llm"

    seed = _stable_seed(idea_clean, g["id"])
    label = g["label_ar"] if language.lower().startswith("ar") else g["label_en"]
    title = _title_from_idea(idea_clean, label)
    synopsis = _synopsis(idea_clean, g, true_story_mode)

    beats = [
        {
            "id": b["id"],
            "title": b["title"],
            "summary": b["summary"].replace("the subject", _slug_words(idea_clean, 4)),
        }
        for b in g["beats"]
    ]

    scenes: list[dict[str, Any]] = []
    idea_snip = _slug_words(idea_clean, 12)
    for idx, bp in enumerate(g["scene_blueprints"]):
        tag = _apply_true_story_tags(bp["content_tag"], true_story_mode)
        script = bp["script_text"]
        if "{idea}" not in script:
            script = f"{script} Subject: {idea_snip}."
        prompt = f"{bp['prompt']}, {g['prompt_suffix']}, subject: {idea_snip}"
        scenes.append(
            {
                "order_index": idx,
                "title": bp["title"],
                "beat_id": bp["beat_id"],
                "script_text": script,
                "camera": bp["camera"] or g["camera_default"],
                "lighting": bp["lighting"] or g["lighting_default"],
                "prompt": prompt,
                "content_tag": tag,
                "duration_hint_sec": bp["duration_hint_sec"],
                "status": "draft",
            }
        )

    return {
        "title": title,
        "synopsis": synopsis,
        "genre": g["id"],
        "true_story_mode": true_story_mode,
        "beats": beats,
        "scenes": scenes,
        "generator": used_backend,
        "generator_notes": backend_notes,
        "seed": seed,
        "language": language,
        "editable": True,
        "schema_version": 4,
    }


__all__ = ["generate_story_draft", "list_genres", "GENRE_IDS", "CONTENT_TAGS"]
