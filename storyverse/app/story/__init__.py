"""Phase 4 — story / script / scene generation (template-first, no ML by default)."""

from app.story.generator import generate_story_draft, list_genres
from app.story.templates import GENRE_IDS

__all__ = ["generate_story_draft", "list_genres", "GENRE_IDS"]
