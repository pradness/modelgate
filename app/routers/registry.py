from fastapi import APIRouter, Depends, HTTPException
from app.schemas import ModelResponse, ModelCreate, ModelUpdate
from app.database import get_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import ModelRegistry
from app.routers.auth import get_current_user

router = APIRouter(prefix="/models", tags=["models"], dependencies=[Depends(get_current_user)])

@router.post("/", response_model=ModelResponse)
async def create_model(
    model: ModelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    db_model = ModelRegistry(**model.model_dump())
    db.add(db_model)
    await db.commit()
    await db.refresh(db_model)
    return db_model

@router.get("/", response_model = list[ModelResponse])
async def list_models(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    result = await db.execute(
        select(ModelRegistry)
    )
    return result.scalars().all()

@router.get("/{model_id}/{version}", response_model=ModelResponse)
async def get_model(
    model_id: int,
    version: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    result = await db.execute(
        select(ModelRegistry).where(ModelRegistry.id == model_id and ModelRegistry.version == version)
    )
    model = result.scalar_one_or_none()

    if model is None:
        raise HTTPException(status_code=404, detail=f"Model with id {model_id} and version {version} not found")

    return model

@router.patch("/{model_id}/{version}", response_model=ModelResponse)
async def update_model(
    model_id: int,
    version: str,
    update: ModelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    result = await db.execute(
        select(ModelRegistry).where(ModelRegistry.id == model_id and ModelRegistry.version == version)
    )

    model = result.scalar_one_or_none()

    if model is None:
        raise HTTPException(status_code=404, detail=f"Model with id {model_id} and version {version} not found")

    data = update.model_dump(exclude_unset=True)
    
    for key, value in data.items():
        setattr(model, key, value)

    await db.commit()
    await db.refresh(model)
    return model