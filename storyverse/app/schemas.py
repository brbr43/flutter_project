"""Pydantic request/response schemas — Phase 3 + Phase 4 story/script."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Projects ---


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    idea: str = ""
    genre: str = "drama"
    true_story_mode: bool = False


class ProjectOut(ORMModel):
    id: int
    name: str
    description: str
    idea: str = ""
    genre: str = "drama"
    true_story_mode: bool = False
    script_title: str = ""
    synopsis: str = ""
    beats: Optional[list[Any]] = None
    generator: str = "template"
    story_meta: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


# --- Scenes ---


class SceneCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    order_index: int = 0
    script_text: str = ""
    prompt: str = ""
    camera: str = ""
    lighting: str = ""
    beat_id: str = ""
    content_tag: str = "fiction"
    duration_hint_sec: int = 5
    status: str = "draft"
    meta: dict[str, Any] = Field(default_factory=dict)


class SceneUpdate(BaseModel):
    """Partial update for manual scene editing."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    order_index: Optional[int] = None
    script_text: Optional[str] = None
    prompt: Optional[str] = None
    camera: Optional[str] = None
    lighting: Optional[str] = None
    beat_id: Optional[str] = None
    content_tag: Optional[str] = None
    duration_hint_sec: Optional[int] = None
    status: Optional[str] = None
    meta: Optional[dict[str, Any]] = None


class SceneOut(ORMModel):
    id: int
    project_id: int
    title: str
    order_index: int
    script_text: str
    prompt: str
    camera: str = ""
    lighting: str = ""
    beat_id: str = ""
    content_tag: str = "fiction"
    duration_hint_sec: int = 5
    meta: Optional[dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime


class SceneReorder(BaseModel):
    """Reorder scenes by providing the full ordered list of scene ids."""

    scene_ids: list[int] = Field(min_length=1)


# --- Story / script (Phase 4) ---

GenreId = Literal[
    "documentary",
    "hollywood",
    "mystery",
    "historical",
    "drama",
    "adventure",
]


class StoryGenerateRequest(BaseModel):
    idea: str = Field(min_length=1)
    genre: GenreId = "drama"
    true_story_mode: bool = False
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    language: str = "en"
    preferred_backend: Literal["auto", "template", "local_llm", "cloud_llm"] = "auto"
    replace_scenes: bool = True


class BeatOut(BaseModel):
    id: str
    title: str
    summary: str


class StoryDraftOut(BaseModel):
    """Editable JSON story draft — exit criterion for Phase 4."""

    project_id: int
    title: str
    synopsis: str
    genre: str
    true_story_mode: bool
    beats: list[BeatOut]
    scenes: list[SceneOut]
    generator: str
    generator_notes: str = ""
    seed: str = ""
    language: str = "en"
    editable: bool = True
    schema_version: int = 4


class StoryUpdate(BaseModel):
    """Manual edit of script-level fields (title / synopsis / beats)."""

    title: Optional[str] = None
    synopsis: Optional[str] = None
    beats: Optional[list[dict[str, Any]]] = None
    idea: Optional[str] = None
    genre: Optional[str] = None
    true_story_mode: Optional[bool] = None


class GenreOut(BaseModel):
    id: str
    label_en: str
    label_ar: str
    tone: str
    beat_count: int
    default_scene_count: int


class LLMGateOut(BaseModel):
    local_allowed: bool
    cloud_allowed: bool
    cloud_key_present: bool
    active_backend: str
    notes: str


# --- Characters ---


class CharacterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    meta: dict[str, Any] = Field(default_factory=dict)


class CharacterOut(ORMModel):
    id: int
    project_id: int
    name: str
    description: str
    meta: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


# --- Assets ---


class AssetCreate(BaseModel):
    kind: str = "other"
    path: str
    scene_id: Optional[int] = None
    character_id: Optional[int] = None
    meta: dict[str, Any] = Field(default_factory=dict)


class AssetOut(ORMModel):
    id: int
    project_id: int
    scene_id: Optional[int]
    character_id: Optional[int]
    kind: str
    path: str
    meta: Optional[dict[str, Any]] = None
    created_at: datetime


# --- Jobs ---

JobStatus = Literal["queued", "running", "done", "failed"]


class JobCreate(BaseModel):
    job_type: str = "fake"
    scene_id: Optional[int] = None
    payload: dict[str, Any] = Field(default_factory=dict)


class JobOut(ORMModel):
    id: int
    project_id: int
    scene_id: Optional[int]
    job_type: str
    status: str
    payload: Optional[dict[str, Any]] = None
    result: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


# --- Settings ---


class SettingUpsert(BaseModel):
    key: str = Field(min_length=1, max_length=120)
    value: dict[str, Any] = Field(default_factory=dict)


class SettingOut(ORMModel):
    id: int
    key: str
    value: Optional[dict[str, Any]] = None
    updated_at: datetime


# --- Health / meta ---


class HealthOut(BaseModel):
    status: str
    version: str
    root: str
    db_path: str
    queue_worker: str
    story_backend: str = "template"
    allow_local_llm: bool = False
    allow_cloud_llm: bool = False
