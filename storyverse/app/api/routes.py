"""HTTP endpoints — Phase 3–6 (story + images + short clips)."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.image.adapter import ASSET_KIND_SCENE_IMAGE, ensure_character_ref_stub
from app.image.workflow import DEFAULT_CHECKPOINT
from app.models import Asset, Character, Job, Project, Scene, Setting, utcnow
from app.paths import ensure_project_layout
from app.queue import job_queue
from app.schemas import (
    AssetCreate,
    AssetOut,
    CharacterCreate,
    CharacterOut,
    CharacterRefStubOut,
    CharacterUpdate,
    GenreOut,
    HealthOut,
    ImageGenerateOut,
    ImageGenerateRequest,
    JobCreate,
    JobOut,
    LLMGateOut,
    ProjectCreate,
    ProjectOut,
    SceneCreate,
    SceneOut,
    SceneReorder,
    SceneUpdate,
    SettingOut,
    SettingUpsert,
    StoryDraftOut,
    StoryGenerateRequest,
    StoryUpdate,
    VideoGateOut,
    VideoGenerateOut,
    VideoGenerateRequest,
)
from app.story.generator import generate_story_draft, list_genres
from app.story.llm import inspect_llm_gates
from app.story.templates import CONTENT_TAGS, GENRE_IDS
from app.video.adapter import ASSET_KIND_SCENE_CLIP
from app.video.gates import KNOWN_ENGINES, assert_no_download_urls, inspect_video_gates

router = APIRouter()


# ----- Health -----


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    settings = get_settings()
    gate = inspect_llm_gates(settings)
    vgate = inspect_video_gates(settings)
    return HealthOut(
        status="ok",
        version=settings.api_version,
        root=str(settings.root),
        db_path=str(settings.db_path),
        queue_worker="single-in-process",
        story_backend=gate.active_backend,
        allow_local_llm=settings.allow_local_llm,
        allow_cloud_llm=bool(settings.allow_cloud_llm and (settings.cloud_llm_api_key or "").strip()),
        comfyui_base_url=settings.comfyui_base_url,
        comfyui_checkpoint=settings.comfyui_checkpoint,
        image_engine="comfyui",
        video_engine=vgate.engine,
        allow_ai_video=vgate.allow_ai_video,
        allow_video_model_download=vgate.allow_video_model_download,
        ai_video_active=vgate.ai_video_active,
        video_is_fallback=vgate.is_fallback,
    )


@router.get("/video/gates", response_model=VideoGateOut)
async def video_gates() -> VideoGateOut:
    g = inspect_video_gates()
    return VideoGateOut(**g.as_dict())


@router.get("/story/llm-gates", response_model=LLMGateOut)
async def story_llm_gates() -> LLMGateOut:
    g = inspect_llm_gates()
    return LLMGateOut(
        local_allowed=g.local_allowed,
        cloud_allowed=g.cloud_allowed,
        cloud_key_present=g.cloud_key_present,
        active_backend=g.active_backend,
        notes=g.notes,
    )


@router.get("/story/genres", response_model=list[GenreOut])
async def story_genres() -> list[GenreOut]:
    return [GenreOut(**g) for g in list_genres()]


# ----- Projects -----


@router.post("/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    session: AsyncSession = Depends(get_session),
) -> Project:
    genre = (body.genre or "drama").strip().lower()
    if genre not in GENRE_IDS:
        raise HTTPException(status_code=400, detail=f"Unknown genre. Allowed: {', '.join(GENRE_IDS)}")
    project = Project(
        name=body.name.strip(),
        description=body.description,
        idea=body.idea or "",
        genre=genre,
        true_story_mode=body.true_story_mode,
    )
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


# ----- Story generate / get / update -----


def _scene_to_dict_fields(s: dict[str, Any]) -> dict[str, Any]:
    tag = (s.get("content_tag") or "fiction").lower()
    if tag not in CONTENT_TAGS:
        tag = "fiction"
    return {
        "title": str(s.get("title") or "Untitled").strip()[:200],
        "order_index": int(s.get("order_index") or 0),
        "script_text": str(s.get("script_text") or ""),
        "prompt": str(s.get("prompt") or ""),
        "camera": str(s.get("camera") or ""),
        "lighting": str(s.get("lighting") or ""),
        "beat_id": str(s.get("beat_id") or ""),
        "content_tag": tag,
        "duration_hint_sec": int(s.get("duration_hint_sec") or 5),
        "status": str(s.get("status") or "draft"),
        "meta": dict(s.get("meta") or {}),
    }


async def _persist_draft(
    session: AsyncSession,
    project: Project,
    draft: dict[str, Any],
    *,
    replace_scenes: bool,
) -> list[Scene]:
    project.idea = draft.get("idea") or project.idea
    project.genre = draft["genre"]
    project.true_story_mode = bool(draft["true_story_mode"])
    project.script_title = draft["title"]
    project.synopsis = draft["synopsis"]
    project.beats = draft["beats"]
    project.generator = draft["generator"]
    project.story_meta = {
        "seed": draft.get("seed"),
        "generator_notes": draft.get("generator_notes"),
        "language": draft.get("language"),
        "schema_version": draft.get("schema_version", 4),
        "editable": True,
    }
    project.updated_at = utcnow()
    if not project.name or project.name.startswith("Story "):
        # Keep user-provided names; auto-name only blanks
        pass
    if replace_scenes:
        await session.execute(delete(Scene).where(Scene.project_id == project.id))
        await session.flush()
        scenes: list[Scene] = []
        for raw in draft["scenes"]:
            fields = _scene_to_dict_fields(raw)
            scene = Scene(project_id=project.id, **fields)
            session.add(scene)
            scenes.append(scene)
        await session.commit()
        for sc in scenes:
            await session.refresh(sc)
        return scenes

    await session.commit()
    result = await session.execute(
        select(Scene).where(Scene.project_id == project.id).order_by(Scene.order_index, Scene.id)
    )
    return list(result.scalars())


def _story_out(project: Project, scenes: list[Scene]) -> StoryDraftOut:
    meta = project.story_meta or {}
    return StoryDraftOut(
        project_id=project.id,
        title=project.script_title or project.name,
        synopsis=project.synopsis or "",
        genre=project.genre,
        true_story_mode=bool(project.true_story_mode),
        beats=list(project.beats or []),
        scenes=scenes,
        generator=project.generator or "template",
        generator_notes=str(meta.get("generator_notes") or ""),
        seed=str(meta.get("seed") or ""),
        language=str(meta.get("language") or "en"),
        editable=True,
        schema_version=int(meta.get("schema_version") or 4),
    )


@router.post(
    "/story/generate",
    response_model=StoryDraftOut,
    status_code=status.HTTP_201_CREATED,
)
async def generate_story(
    body: StoryGenerateRequest,
    session: AsyncSession = Depends(get_session),
) -> StoryDraftOut:
    """Idea → script draft → scene list. Template generator by default (no ML)."""
    try:
        draft = generate_story_draft(
            body.idea,
            body.genre,
            true_story_mode=body.true_story_mode,
            preferred_backend=body.preferred_backend,
            language=body.language,
        )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    draft["idea"] = body.idea.strip()

    if body.project_id is not None:
        project = await session.get(Project, body.project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")
    else:
        name = (body.project_name or draft["title"]).strip()[:200]
        project = Project(
            name=name or "Untitled Story",
            description=body.idea.strip()[:500],
            idea=body.idea.strip(),
            genre=draft["genre"],
            true_story_mode=body.true_story_mode,
        )
        session.add(project)
        await session.flush()
        ensure_project_layout(project.id)

    scenes = await _persist_draft(
        session, project, draft, replace_scenes=body.replace_scenes
    )
    ensure_project_layout(project.id)
    await session.refresh(project)
    return _story_out(project, scenes)


@router.post(
    "/projects/{project_id}/story/generate",
    response_model=StoryDraftOut,
    status_code=status.HTTP_201_CREATED,
)
async def generate_story_for_project(
    project_id: int,
    body: StoryGenerateRequest,
    session: AsyncSession = Depends(get_session),
) -> StoryDraftOut:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    idea = (body.idea or project.idea or "").strip()
    if not idea:
        raise HTTPException(status_code=400, detail="idea required (body or project.idea)")
    req = body.model_copy(update={"idea": idea, "project_id": project_id})
    return await generate_story(req, session)


@router.get("/projects/{project_id}/story", response_model=StoryDraftOut)
async def get_story(
    project_id: int,
    session: AsyncSession = Depends(get_session),
) -> StoryDraftOut:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    result = await session.execute(
        select(Scene).where(Scene.project_id == project_id).order_by(Scene.order_index, Scene.id)
    )
    scenes = list(result.scalars())
    return _story_out(project, scenes)


@router.put("/projects/{project_id}/story", response_model=StoryDraftOut)
async def update_story(
    project_id: int,
    body: StoryUpdate,
    session: AsyncSession = Depends(get_session),
) -> StoryDraftOut:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if body.title is not None:
        project.script_title = body.title.strip()[:300]
    if body.synopsis is not None:
        project.synopsis = body.synopsis
    if body.beats is not None:
        project.beats = body.beats
    if body.idea is not None:
        project.idea = body.idea
    if body.genre is not None:
        g = body.genre.strip().lower()
        if g not in GENRE_IDS:
            raise HTTPException(status_code=400, detail=f"Unknown genre. Allowed: {', '.join(GENRE_IDS)}")
        project.genre = g
    if body.true_story_mode is not None:
        project.true_story_mode = body.true_story_mode
    project.updated_at = utcnow()
    await session.commit()
    await session.refresh(project)
    result = await session.execute(
        select(Scene).where(Scene.project_id == project_id).order_by(Scene.order_index, Scene.id)
    )
    return _story_out(project, list(result.scalars()))


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
    tag = (body.content_tag or "fiction").lower()
    if tag not in CONTENT_TAGS:
        raise HTTPException(
            status_code=400,
            detail=f"content_tag must be one of: {', '.join(CONTENT_TAGS)}",
        )
    scene = Scene(
        project_id=project_id,
        title=body.title.strip(),
        order_index=body.order_index,
        script_text=body.script_text,
        prompt=body.prompt,
        camera=body.camera,
        lighting=body.lighting,
        beat_id=body.beat_id,
        content_tag=tag,
        duration_hint_sec=body.duration_hint_sec,
        status=body.status,
        meta=body.meta,
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


@router.patch("/scenes/{scene_id}", response_model=SceneOut)
async def update_scene(
    scene_id: int,
    body: SceneUpdate,
    session: AsyncSession = Depends(get_session),
) -> Scene:
    scene = await session.get(Scene, scene_id)
    if scene is None:
        raise HTTPException(status_code=404, detail="Scene not found")
    data = body.model_dump(exclude_unset=True)
    if "content_tag" in data and data["content_tag"] is not None:
        tag = str(data["content_tag"]).lower()
        if tag not in CONTENT_TAGS:
            raise HTTPException(
                status_code=400,
                detail=f"content_tag must be one of: {', '.join(CONTENT_TAGS)}",
            )
        data["content_tag"] = tag
    if "title" in data and data["title"] is not None:
        data["title"] = str(data["title"]).strip()
    for key, value in data.items():
        setattr(scene, key, value)
    scene.updated_at = utcnow()
    await session.commit()
    await session.refresh(scene)
    return scene


@router.put("/projects/{project_id}/scenes/reorder", response_model=list[SceneOut])
async def reorder_scenes(
    project_id: int,
    body: SceneReorder,
    session: AsyncSession = Depends(get_session),
) -> list[Scene]:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    result = await session.execute(select(Scene).where(Scene.project_id == project_id))
    scenes = {s.id: s for s in result.scalars()}
    if set(body.scene_ids) != set(scenes.keys()):
        raise HTTPException(
            status_code=400,
            detail="scene_ids must include every scene in the project exactly once",
        )
    for index, sid in enumerate(body.scene_ids):
        scenes[sid].order_index = index
        scenes[sid].updated_at = utcnow()
    await session.commit()
    ordered = await session.execute(
        select(Scene).where(Scene.project_id == project_id).order_by(Scene.order_index, Scene.id)
    )
    return list(ordered.scalars())


# ----- Characters -----


def _merge_character_meta(
    base: dict[str, Any] | None,
    *,
    visual_prompt: str | None = None,
    reference_notes: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    meta = dict(base or {})
    if extra:
        meta.update(extra)
    if visual_prompt is not None and visual_prompt.strip():
        meta["visual_prompt"] = visual_prompt.strip()
    if reference_notes is not None and reference_notes.strip():
        meta["reference_notes"] = reference_notes.strip()
    return meta


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
        meta=_merge_character_meta(
            body.meta,
            visual_prompt=body.visual_prompt,
            reference_notes=body.reference_notes,
        ),
    )
    session.add(character)
    await session.commit()
    await session.refresh(character)
    # Light stub folders (optional refs) — no generation
    ensure_character_ref_stub(project_id, character.id)
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


@router.patch("/characters/{character_id}", response_model=CharacterOut)
async def update_character(
    character_id: int,
    body: CharacterUpdate,
    session: AsyncSession = Depends(get_session),
) -> Character:
    character = await session.get(Character, character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    if body.name is not None:
        character.name = body.name.strip()
    if body.description is not None:
        character.description = body.description
    base_meta = dict(character.meta or {})
    if body.meta is not None:
        base_meta.update(body.meta)
    character.meta = _merge_character_meta(
        base_meta,
        visual_prompt=body.visual_prompt,
        reference_notes=body.reference_notes,
    )
    character.updated_at = utcnow()
    await session.commit()
    await session.refresh(character)
    return character


@router.post(
    "/characters/{character_id}/ref-stub",
    response_model=CharacterRefStubOut,
)
async def character_ref_stub(
    character_id: int,
    session: AsyncSession = Depends(get_session),
) -> CharacterRefStubOut:
    """Ensure light character reference folder exists (no image gen / no downloads)."""
    character = await session.get(Character, character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    info = ensure_character_ref_stub(character.project_id, character.id)
    return CharacterRefStubOut(
        character_id=character.id,
        project_id=character.project_id,
        refs_dir=info["refs_dir"],
        readme=info["readme"],
        stub=True,
    )


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


# ----- Scene image generation (Phase 5) -----


def _image_payload(body: ImageGenerateRequest) -> dict[str, Any]:
    settings = get_settings()
    payload: dict[str, Any] = {
        "character_ids": list(body.character_ids or []),
        "extra_prompt": body.extra_prompt or "",
    }
    if body.prompt_override is not None:
        payload["prompt_override"] = body.prompt_override
    if body.negative_prompt is not None:
        payload["negative_prompt"] = body.negative_prompt
    if body.seed is not None:
        payload["seed"] = body.seed
    if body.steps is not None:
        payload["steps"] = body.steps
    if body.cfg is not None:
        payload["cfg"] = body.cfg
    if body.width is not None:
        payload["width"] = body.width
    if body.height is not None:
        payload["height"] = body.height
    ckpt = (body.checkpoint or settings.comfyui_checkpoint or DEFAULT_CHECKPOINT).strip()
    if "/" in ckpt or "\\" in ckpt or ckpt.startswith("http"):
        raise HTTPException(
            status_code=400,
            detail=(
                "checkpoint must be a local ComfyUI filename "
                f"(default {DEFAULT_CHECKPOINT}); no download URLs"
            ),
        )
    payload["checkpoint"] = ckpt
    return payload


async def _enqueue_image_job(
    session: AsyncSession,
    *,
    project_id: int,
    scene_id: int,
    body: ImageGenerateRequest,
) -> Job:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    scene = await session.get(Scene, scene_id)
    if scene is None or scene.project_id != project_id:
        raise HTTPException(status_code=404, detail="Scene not found in this project")
    if body.character_ids:
        result = await session.execute(
            select(Character).where(
                Character.project_id == project_id,
                Character.id.in_(body.character_ids),
            )
        )
        found = {c.id for c in result.scalars()}
        missing = [cid for cid in body.character_ids if cid not in found]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"character_ids not in this project: {missing}",
            )
    job = Job(
        project_id=project_id,
        scene_id=scene_id,
        job_type="image_generate",
        status="queued",
        payload=_image_payload(body),
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    await job_queue.enqueue(job.id)
    return job


@router.post(
    "/scenes/{scene_id}/generate-image",
    response_model=ImageGenerateOut,
    status_code=status.HTTP_201_CREATED,
)
async def generate_scene_image_job(
    scene_id: int,
    body: ImageGenerateRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> ImageGenerateOut:
    """Queue ComfyUI image generation for one scene (keeps prior versions)."""
    scene = await session.get(Scene, scene_id)
    if scene is None:
        raise HTTPException(status_code=404, detail="Scene not found")
    job = await _enqueue_image_job(
        session,
        project_id=scene.project_id,
        scene_id=scene_id,
        body=body or ImageGenerateRequest(),
    )
    return ImageGenerateOut(job=job, scene_id=scene_id, project_id=scene.project_id)


@router.post(
    "/projects/{project_id}/scenes/{scene_id}/generate-image",
    response_model=ImageGenerateOut,
    status_code=status.HTTP_201_CREATED,
)
async def generate_project_scene_image_job(
    project_id: int,
    scene_id: int,
    body: ImageGenerateRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> ImageGenerateOut:
    job = await _enqueue_image_job(
        session,
        project_id=project_id,
        scene_id=scene_id,
        body=body or ImageGenerateRequest(),
    )
    return ImageGenerateOut(job=job, scene_id=scene_id, project_id=project_id)


@router.get("/scenes/{scene_id}/images", response_model=list[AssetOut])
async def list_scene_images(
    scene_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[Asset]:
    scene = await session.get(Scene, scene_id)
    if scene is None:
        raise HTTPException(status_code=404, detail="Scene not found")
    result = await session.execute(
        select(Asset)
        .where(Asset.scene_id == scene_id, Asset.kind == ASSET_KIND_SCENE_IMAGE)
        .order_by(Asset.id)
    )
    return list(result.scalars())


# ----- Scene clip generation (Phase 6) -----


def _video_payload(body: VideoGenerateRequest) -> dict[str, Any]:
    settings = get_settings()
    payload: dict[str, Any] = {}
    engine = (body.engine or settings.video_engine or "ffmpeg_kenburns").strip().lower()
    if engine not in KNOWN_ENGINES:
        raise HTTPException(
            status_code=400,
            detail=f"engine must be one of: {', '.join(sorted(KNOWN_ENGINES))}",
        )
    payload["engine"] = engine
    if body.duration_sec is not None:
        payload["duration_sec"] = body.duration_sec
    if body.fps is not None:
        payload["fps"] = body.fps
    if body.width is not None:
        payload["width"] = body.width
    if body.height is not None:
        payload["height"] = body.height
    if body.source_image_path is not None:
        try:
            assert_no_download_urls(body.source_image_path, field="source_image_path")
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        payload["source_image_path"] = body.source_image_path
    if body.model is not None:
        try:
            assert_no_download_urls(body.model, field="model")
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if "/" in body.model or "\\" in body.model:
            raise HTTPException(
                status_code=400,
                detail="model must be a local filename only (no paths / no download URLs)",
            )
        payload["model"] = body.model.strip()
    return payload


async def _enqueue_video_job(
    session: AsyncSession,
    *,
    project_id: int,
    scene_id: int,
    body: VideoGenerateRequest,
) -> Job:
    project = await session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    scene = await session.get(Scene, scene_id)
    if scene is None or scene.project_id != project_id:
        raise HTTPException(status_code=404, detail="Scene not found in this project")
    job = Job(
        project_id=project_id,
        scene_id=scene_id,
        job_type="video_generate",
        status="queued",
        payload=_video_payload(body),
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    await job_queue.enqueue(job.id)
    return job


@router.post(
    "/scenes/{scene_id}/generate-clip",
    response_model=VideoGenerateOut,
    status_code=status.HTTP_201_CREATED,
)
async def generate_scene_clip_job(
    scene_id: int,
    body: VideoGenerateRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> VideoGenerateOut:
    """Queue short clip for one scene (default: FFmpeg Ken Burns fallback, not AI)."""
    scene = await session.get(Scene, scene_id)
    if scene is None:
        raise HTTPException(status_code=404, detail="Scene not found")
    job = await _enqueue_video_job(
        session,
        project_id=scene.project_id,
        scene_id=scene_id,
        body=body or VideoGenerateRequest(),
    )
    return VideoGenerateOut(job=job, scene_id=scene_id, project_id=scene.project_id)


@router.post(
    "/projects/{project_id}/scenes/{scene_id}/generate-clip",
    response_model=VideoGenerateOut,
    status_code=status.HTTP_201_CREATED,
)
async def generate_project_scene_clip_job(
    project_id: int,
    scene_id: int,
    body: VideoGenerateRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> VideoGenerateOut:
    job = await _enqueue_video_job(
        session,
        project_id=project_id,
        scene_id=scene_id,
        body=body or VideoGenerateRequest(),
    )
    return VideoGenerateOut(job=job, scene_id=scene_id, project_id=project_id)


@router.get("/scenes/{scene_id}/clips", response_model=list[AssetOut])
async def list_scene_clips(
    scene_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[Asset]:
    scene = await session.get(Scene, scene_id)
    if scene is None:
        raise HTTPException(status_code=404, detail="Scene not found")
    result = await session.execute(
        select(Asset)
        .where(Asset.scene_id == scene_id, Asset.kind == ASSET_KIND_SCENE_CLIP)
        .order_by(Asset.id)
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
    allowed = {"fake", "image_generate", "video_generate"}
    if body.job_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"job_type must be one of: {', '.join(sorted(allowed))}",
        )
    if body.job_type == "image_generate" and body.scene_id is None:
        raise HTTPException(status_code=400, detail="image_generate requires scene_id")
    if body.job_type == "video_generate" and body.scene_id is None:
        raise HTTPException(status_code=400, detail="video_generate requires scene_id")
    payload = dict(body.payload or {})
    if body.job_type == "image_generate" and "checkpoint" not in payload:
        payload["checkpoint"] = get_settings().comfyui_checkpoint
    if body.job_type == "video_generate" and "engine" not in payload:
        payload["engine"] = get_settings().video_engine
    if body.job_type == "video_generate":
        eng = str(payload.get("engine") or "").strip().lower()
        if eng and eng not in KNOWN_ENGINES:
            raise HTTPException(
                status_code=400,
                detail=f"engine must be one of: {', '.join(sorted(KNOWN_ENGINES))}",
            )
        for key in ("source_image_path", "model"):
            if key in payload and payload[key] is not None:
                try:
                    assert_no_download_urls(str(payload[key]), field=key)
                except RuntimeError as exc:
                    raise HTTPException(status_code=400, detail=str(exc)) from exc
    job = Job(
        project_id=project_id,
        scene_id=body.scene_id,
        job_type=body.job_type,
        status="queued",
        payload=payload,
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
