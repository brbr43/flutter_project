"""File-layout helpers under a configurable StoryVerse root."""

from __future__ import annotations

from pathlib import Path

from app.config import Settings, get_settings


def ensure_runtime_dirs(settings: Settings | None = None) -> dict[str, Path]:
    """Create top-level runtime folders (data/, projects/). No model downloads."""
    s = settings or get_settings()
    created = {
        "root": s.root,
        "data": s.data_dir,
        "projects": s.projects_dir,
    }
    for path in (s.root, s.data_dir, s.projects_dir):
        path.mkdir(parents=True, exist_ok=True)
    return created


def project_dir(project_id: int | str, settings: Settings | None = None) -> Path:
    s = settings or get_settings()
    return s.projects_dir / str(project_id)


def ensure_project_layout(project_id: int | str, settings: Settings | None = None) -> dict[str, Path]:
    """
    Layout per project:

        {STORYVERSE_ROOT}/projects/{id}/
          scenes/
          characters/
          assets/
          exports/
          scratch/
    """
    s = settings or get_settings()
    ensure_runtime_dirs(s)
    base = project_dir(project_id, s)
    layout = {
        "root": base,
        "scenes": base / "scenes",
        "characters": base / "characters",
        "assets": base / "assets",
        "exports": base / "exports",
        "scratch": base / "scratch",
    }
    for path in layout.values():
        path.mkdir(parents=True, exist_ok=True)
    return layout


def scene_dir(project_id: int | str, scene_id: int | str, settings: Settings | None = None) -> Path:
    return ensure_project_layout(project_id, settings)["scenes"] / str(scene_id)


def asset_path(
    project_id: int | str,
    filename: str,
    *,
    settings: Settings | None = None,
) -> Path:
    return ensure_project_layout(project_id, settings)["assets"] / filename
