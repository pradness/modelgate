from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ModelVersions, ModelStatus, User
from app.routers.auth import get_current_user
from app.routers.model_queries import get_model_version, get_owned_model
from app.schemas import (
    ModelDetailResponse,
    ModelVersionCreate,
    ModelVersionResponse,
    ModelVersionUpdate,
)

router = APIRouter(
    prefix="/models/{model_id}/versions",
    tags=["versions"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    "/", response_model=ModelVersionResponse, status_code=status.HTTP_201_CREATED
)
async def create_model_version(
    model_id: int,
    modelversion: ModelVersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    model = await get_owned_model(db, model_id, current_user.id)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
        )

    existing = await get_model_version(db, model_id, modelversion.version)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Model with this version already exists.",
        )

    db_model = ModelVersions(**modelversion.model_dump(), model_id=model_id)
    db.add(db_model)
    await db.commit()
    await db.refresh(db_model)
    return db_model


@router.get("/", response_model=ModelDetailResponse)
async def list_model_versions(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    model = await get_owned_model(db, model_id, current_user.id, include_versions=True)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found.",
        )
    return model


@router.get("/latest", response_model=ModelVersionResponse)
async def get_latest_model_version(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    model = await get_owned_model(db, model_id, current_user.id)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found.",
        )

    result = await db.execute(
        select(ModelVersions)
        .where(ModelVersions.model_id == model_id, ModelVersions.status != ModelStatus.DELETED,)
        .order_by(ModelVersions.created_at.desc())
    )
    latest_version = result.scalars().first()
    if latest_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No versions found for this model.",
        )

    return latest_version


@router.get("/{version}", response_model=ModelVersionResponse)
async def get_version(
    model_id: int,
    version: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    model = await get_owned_model(db, model_id, current_user.id)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found.",
        )

    version_model = await get_model_version(db, model_id, version)
    if version_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Version not found."
        )

    return version_model


@router.patch("/{version}", response_model=ModelVersionResponse)
async def update_model_version(
    model_id: int,
    version: str,
    update: ModelVersionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    model = await get_owned_model(db, model_id, current_user.id)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found.",
        )

    version_model = await get_model_version(db, model_id, version)
    if version_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Version not found."
        )

    data = update.model_dump(exclude_unset=True)

    if "version" in data and data["version"] != version:
        existing = await get_model_version(db, model_id, data["version"])
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Version already exists.",
            )

    for field, value in data.items():
        setattr(version_model, field, value)

    await db.commit()
    await db.refresh(version_model)
    return version_model


@router.delete("/{version}", response_model=ModelVersionResponse, status_code=status.HTTP_200_OK)
async def delete_version(
    model_id: int,
    version: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    model = await get_owned_model(db, model_id, current_user.id)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found.",
        )

    version_model = await get_model_version(db, model_id, version)
    if version_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Version not found."
        )

    version_model.status = ModelStatus.DELETED
    await db.commit()
    return version_model
