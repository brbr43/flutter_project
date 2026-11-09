"""Pydantic request/response schemas."""

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


class ProjectOut(ORMModel):
    id: int
    name: str
    description: str
    created_at: datetime
    updated_at: datetime


# --- Scenes ---


class SceneCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    order_index: int = 0
    script_text: str = ""
    prompt: str = ""
    status: str = "draft"


class SceneOut(ORMModel):
    id: int
    project_id: int
    title: str
    order_index: int
    script_text: str
    prompt: str
    status: str
    created_at: datetime
    updated_at: datetime


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
