"""All Phase 3 HTTP endpoints in one router module."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.models import Asset, Character, Job, Project, Scene, Setting
from app.paths import ensure_project_layout
from app.queue import job_queue
from app.schemas import (
    AssetCreate,
    AssetOut,
    CharacterCreate,
    CharacterOut,
    HealthOut,
    JobCreate,
    JobOut,
    ProjectCreate,
    ProjectOut,
    SceneCreate,
    SceneOut,
    SettingOut,
    SettingUpsert,
)

router = APIRouter()


# ----- Health -----


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    settings = get_settings()
    return HealthOut(
        status="ok",
        version=settings.api_version,
        root=str(settings.root),
        db_path=str(settings.db_path),
        queue_worker="single-in-process",
    )


# ----- Projects -----


@router.post("/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    session: AsyncSession = Depends(get_session),
) -> Project:
    project = Project(name=body.name.strip(), description=body.description)
    session.add(project)
    await session.commit()
    await session.refresh(project)
    ensure_project_layout(project.id)
    return project


@router.get("/projects", response_model=list[ProjectOut])
async def list_projects(session: AsyncSession = Depends(get_session)) -> list[Project]:
    result = await session.execute(select(Project).order_by(Project.id))
    return list(result.scalars())


@router.get("/projects/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, session: AsyncSession = Depends(get_session)) -> Project:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ----- Scenes -----


@router.post(
    "/projects/{project_id}/scenes",
    response_model=SceneOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_scene(
    project_id: int,
    body: SceneCreate,
    session: AsyncSession = Depends(get_session),
) -> Scene:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    scene = Scene(
        project_id=project_id,
        title=body.title.strip(),
        order_index=body.order_index,
        script_text=body.script_text,
        prompt=body.prompt,
        status=body.status,
    )
    session.add(scene)
    await session.commit()
    await session.refresh(scene)
    ensure_project_layout(project_id)
    return scene


@router.get("/projects/{project_id}/scenes", response_model=list[SceneOut])
async def list_scenes(
    project_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[Scene]:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    result = await session.execute(
        select(Scene).where(Scene.project_id == project_id).order_by(Scene.order_index, Scene.id)
    )
    return list(result.scalars())


@router.get("/scenes/{scene_id}", response_model=SceneOut)
async def get_scene(scene_id: int, session: AsyncSession = Depends(get_session)) -> Scene:
    scene = await session.get(Scene, scene_id)
    if scene is None:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene


# ----- Characters -----


@router.post(
    "/projects/{project_id}/characters",
    response_model=CharacterOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_character(
    project_id: int,
    body: CharacterCreate,
    session: AsyncSession = Depends(get_session),
) -> Character:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    character = Character(
        project_id=project_id,
        name=body.name.strip(),
        description=body.description,
        meta=body.meta,
    )
    session.add(character)
    await session.commit()
    await session.refresh(character)
    return character


@router.get("/projects/{project_id}/characters", response_model=list[CharacterOut])
async def list_characters(
    project_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[Character]:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    result = await session.execute(
        select(Character).where(Character.project_id == project_id).order_by(Character.id)
    )
    return list(result.scalars())


# ----- Assets -----


@router.post(
    "/projects/{project_id}/assets",
    response_model=AssetOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_asset(
    project_id: int,
    body: AssetCreate,
    session: AsyncSession = Depends(get_session),
) -> Asset:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if body.scene_id is not None:
        scene = await session.get(Scene, body.scene_id)
        if scene is None or scene.project_id != project_id:
            raise HTTPException(status_code=400, detail="scene_id not in this project")
    if body.character_id is not None:
        character = await session.get(Character, body.character_id)
        if character is None or character.project_id != project_id:
            raise HTTPException(status_code=400, detail="character_id not in this project")
    asset = Asset(
        project_id=project_id,
        scene_id=body.scene_id,
        character_id=body.character_id,
        kind=body.kind,
        path=body.path,
        meta=body.meta,
    )
    session.add(asset)
    await session.commit()
    await session.refresh(asset)
    return asset


@router.get("/projects/{project_id}/assets", response_model=list[AssetOut])
async def list_assets(
    project_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[Asset]:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    result = await session.execute(
        select(Asset).where(Asset.project_id == project_id).order_by(Asset.id)
    )
    return list(result.scalars())


# ----- Jobs -----


@router.post(
    "/projects/{project_id}/jobs",
    response_model=JobOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_job(
    project_id: int,
    body: JobCreate,
    session: AsyncSession = Depends(get_session),
) -> Job:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if body.scene_id is not None:
        scene = await session.get(Scene, body.scene_id)
        if scene is None or scene.project_id != project_id:
            raise HTTPException(status_code=400, detail="scene_id not in this project")
    job = Job(
        project_id=project_id,
        scene_id=body.scene_id,
        job_type=body.job_type,
        status="queued",
        payload=body.payload,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    await job_queue.enqueue(job.id)
    return job


@router.get("/projects/{project_id}/jobs", response_model=list[JobOut])
async def list_jobs(
    project_id: int,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    session: AsyncSession = Depends(get_session),
) -> list[Job]:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    stmt = select(Job).where(Job.project_id == project_id).order_by(Job.id)
    if status_filter:
        stmt = stmt.where(Job.status == status_filter)
    result = await session.execute(stmt)
    return list(result.scalars())


@router.get("/jobs/{job_id}", response_model=JobOut)
async def get_job(job_id: int, session: AsyncSession = Depends(get_session)) -> Job:
    job = await session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/queue/status")
async def queue_status() -> dict:
    return {
        "worker": "single-in-process",
        "pending": job_queue.pending_count,
        "current_job_id": job_queue.current_job_id,
    }


# ----- Settings -----


@router.put("/settings/{key}", response_model=SettingOut)
async def upsert_setting(
    key: str,
    body: SettingUpsert,
    session: AsyncSession = Depends(get_session),
) -> Setting:
    if body.key and body.key != key:
        raise HTTPException(status_code=400, detail="key mismatch between path and body")
    result = await session.execute(select(Setting).where(Setting.key == key))
    row = result.scalar_one_or_none()
    if row is None:
        row = Setting(key=key, value=body.value)
        session.add(row)
    else:
        row.value = body.value
    await session.commit()
    await session.refresh(row)
    return row


@router.get("/settings", response_model=list[SettingOut])
async def list_settings(session: AsyncSession = Depends(get_session)) -> list[Setting]:
    result = await session.execute(select(Setting).order_by(Setting.key))
    return list(result.scalars())


@router.get("/settings/{key}", response_model=SettingOut)
async def get_setting(key: str, session: AsyncSession = Depends(get_session)) -> Setting:
    result = await session.execute(select(Setting).where(Setting.key == key))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    return row
