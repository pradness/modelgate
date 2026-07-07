from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ModelRegistry, User
from app.routers.auth import get_current_user
from app.schemas import ModelCreate, ModelResponse, ModelUpdate, ModelDetailResponse

router = APIRouter(
    prefix="/models", tags=["models"], dependencies=[Depends(get_current_user)]
)

async def get_owned_model(
    model_id: int, 
    owner_id: int,
    db: AsyncSession = Depends(get_db),
) -> ModelRegistry:
    result = await db.execute(
        select(ModelRegistry)
        .options(selectinload(ModelRegistry.versions))
        .where(ModelRegistry.id == model_id, ModelRegistry.owner_id == owner_id)
    )
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return model


@router.post("/", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    model: ModelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await db.execute(
        select(ModelRegistry).where(
            ModelRegistry.owner_id == current_user.id,
            ModelRegistry.name == model.name
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            409,
            "Model with this name already exists."
        )
    
    db_model = ModelRegistry(**model.model_dump(), owner_id=current_user.id)

    db.add(db_model)
    await db.commit()
    await db.refresh(db_model)
    return db_model


@router.get("/", response_model=list[ModelResponse])
async def list_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ModelRegistry)
        .options(selectinload(ModelRegistry.versions))
        .where(ModelRegistry.owner_id == current_user.id)
        .order_by(ModelRegistry.name)
    )
    return result.scalars().all()


@router.get("/{model_id}", response_model=ModelDetailResponse)
async def get_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_owned_model(model_id, current_user.id, db)


@router.patch("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: int,
    update: ModelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    model = await get_owned_model(model_id, current_user.id, db)

    data = update.model_dump(exclude_unset=True)

    if "name" in data:
        existing = await db.execute(
            select(ModelRegistry).where(
                ModelRegistry.owner_id == current_user.id,
                ModelRegistry.name == data["name"],
                ModelRegistry.id != model_id,
            )
        )

        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A model with this name already exists.",
            )

    for field, value in data.items():
        setattr(model, field, value)

    await db.commit()
    await db.refresh(model)

    return model