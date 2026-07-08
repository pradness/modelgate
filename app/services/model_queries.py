from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import APIKey, APIUsage, ModelRegistry, ModelStatus, ModelVersions
from app.routers.auth import verify_password


async def get_owned_model(
    db: AsyncSession,
    model_id: int,
    owner_id: int,
    include_versions: bool = False,
) -> ModelRegistry | None:
    stmt = select(ModelRegistry).where(
        ModelRegistry.id == model_id,
        ModelRegistry.owner_id == owner_id,
    )
    if include_versions:
        stmt = stmt.options(selectinload(ModelRegistry.versions))

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_owned_model_by_name(
    db: AsyncSession,
    model_name: str,
    owner_id: int,
    include_versions: bool = False,
) -> ModelRegistry | None:
    stmt = select(ModelRegistry).where(
        ModelRegistry.name == model_name,
        ModelRegistry.owner_id == owner_id,
    )
    if include_versions:
        stmt = stmt.options(selectinload(ModelRegistry.versions))

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_model_version(
    db: AsyncSession,
    model_id: int,
    version: str,
) -> ModelVersions | None:
    result = await db.execute(
        select(ModelVersions).where(
            ModelVersions.model_id == model_id,
            ModelVersions.version == version,
            ModelVersions.status != ModelStatus.DELETED,
        )
    )
    return result.scalar_one_or_none()


async def get_latest_model_version(
    db: AsyncSession,
    model_id: int,
) -> ModelVersions | None:
    result = await db.execute(
        select(ModelVersions)
        .where(
            ModelVersions.model_id == model_id,
            ModelVersions.status != ModelStatus.DELETED,
        )
        .order_by(ModelVersions.created_at.desc())
    )
    return result.scalars().first()


async def get_api_key_by_value(
    db: AsyncSession,
    raw_api_key: str,
) -> APIKey | None:
    result = await db.execute(
        select(APIKey)
        .options(selectinload(APIKey.user))
        .where(APIKey.is_active.is_(True))
    )

    for api_key in result.scalars():
        if verify_password(raw_api_key, api_key.key_hash):
            return api_key

    return None


async def record_api_usage(
    db: AsyncSession,
    user_id: int,
    api_key_id: int,
    model_version_id: int,
    latency_ms: float,
    status_code: int,
    cached: bool,
) -> APIUsage:
    usage = APIUsage(
        user_id=user_id,
        api_key_id=api_key_id,
        model_version_id=model_version_id,
        latency_ms=latency_ms,
        status_code=status_code,
        cached=cached,
    )
    db.add(usage)
    await db.commit()
    await db.refresh(usage)
    return usage
