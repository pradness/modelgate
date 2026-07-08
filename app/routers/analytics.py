from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import APIKey, APIUsage, ModelRegistry, ModelVersions, User
from app.routers.auth import get_current_user
from app.schemas import APIKeyAnalyticsResponse, ModelVersionsAnalyticsResponse

router = APIRouter(
    prefix="/analytics", tags=["analytics"], dependencies=[Depends(get_current_user)]
)


@router.get("/dashboard")
async def dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_requests = await db.scalar(
        select(func.count(APIUsage.id)).where(APIUsage.user_id == current_user.id)
    )

    avg_latency = await db.scalar(
        select(func.avg(APIUsage.latency_ms)).where(APIUsage.user_id == current_user.id)
    )

    cache_hits = await db.scalar(
        select(func.count(APIUsage.id)).where(
            APIUsage.user_id == current_user.id, APIUsage.cached
        )
    )

    active_models = await db.scalar(
        select(func.count(ModelRegistry.id)).where(
            ModelRegistry.owner_id == current_user.id
        )
    )

    cache_rate = (
        (cache_hits / total_requests) * 100  # type: ignore
        if total_requests
        else 0
    )

    return {
        "total_requests": total_requests,
        "average_latency_ms": round(avg_latency or 0, 2),
        "cache_hit_rate": round(cache_rate, 2),
        "active_models": active_models,
    }


@router.get("/usage")
async def usage(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(APIUsage)
        .options(selectinload(APIUsage.model_version))
        .where(APIUsage.user_id == current_user.id)
        .order_by(APIUsage.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/top-models")
async def top_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(
            ModelRegistry.name,
            func.count(APIUsage.id).label("requests"),
        )
        .join(ModelRegistry.versions)
        .join(APIUsage)
        .where(ModelRegistry.owner_id == current_user.id)
        .group_by(ModelRegistry.name)
        .order_by(desc("requests"))
    )
    return [
        {
            "model": row.name,
            "requests": row.requests,
        }
        for row in result
    ]


@router.get("/latency")
async def latency(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(
            func.avg(APIUsage.latency_ms),
            func.min(APIUsage.latency_ms),
            func.max(APIUsage.latency_ms),
        ).where(APIUsage.user_id == current_user.id)
    )

    avg_, min_, max_ = result.one()

    return {
        "average": round(avg_ or 0, 2),
        "minimum": round(min_ or 0, 2),
        "maximum": round(max_ or 0, 2),
    }


@router.get("/models/{model_id}")
async def analytics_for_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    model = await db.scalar(
        select(ModelRegistry).where(
            ModelRegistry.id == model_id,
            ModelRegistry.owner_id == current_user.id,
        )
    )

    if model is None:
        raise HTTPException(404, "Model not found")

    total = await db.scalar(
        select(func.count(APIUsage.id))
        .join(APIUsage.model_version)
        .where(
            APIUsage.user_id == current_user.id,
            ModelVersions.model_id == model_id,
        )
    )

    avg_latency = await db.scalar(
        select(func.avg(APIUsage.latency_ms))
        .join(APIUsage.model_version)
        .where(
            APIUsage.user_id == current_user.id,
            ModelVersions.model_id == model_id,
        )
    )

    cache_hits = await db.scalar(
        select(func.count(APIUsage.id))
        .join(APIUsage.model_version)
        .where(
            APIUsage.user_id == current_user.id,
            ModelVersions.model_id == model_id,
            APIUsage.cached,
        )
    )

    return {
        "model": model.name,
        "requests": total,
        "average_latency_ms": round(avg_latency or 0, 2),
        "cache_hit_rate": round(
            (cache_hits / total * 100) if total else 0,  # type: ignore
            2,
        ),
    }


@router.get(
    "/models/{model_id}/versions", response_model=ModelVersionsAnalyticsResponse
)
async def analytics_for_modelversions(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    model = await db.scalar(
        select(ModelRegistry).where(
            ModelRegistry.id == model_id,
            ModelRegistry.owner_id == current_user.id,
        )
    )

    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    versions = await db.execute(
        select(ModelVersions)
        .where(ModelVersions.model_id == model_id)
        .order_by(desc(ModelVersions.created_at))
    )

    version_rows = []
    for version in versions.scalars().all():
        total = await db.scalar(
            select(func.count(APIUsage.id)).where(
                APIUsage.model_version_id == version.id
            )
        )
        avg_latency = await db.scalar(
            select(func.avg(APIUsage.latency_ms)).where(
                APIUsage.model_version_id == version.id
            )
        )
        cache_hits = await db.scalar(
            select(func.count(APIUsage.id)).where(
                APIUsage.model_version_id == version.id,
                APIUsage.cached.is_(True),
            )
        )

        version_rows.append(
            {
                "version": version.version,
                "status": version.status,
                "requests": int(total or 0),
                "average_latency_ms": round(avg_latency or 0, 2),
                "cache_hit_rate": round(
                    ((cache_hits or 0) / total * 100) if total else 0,
                    2,
                ),
            }
        )

    return {
        "model": model.name,
        "versions": version_rows,
    }


@router.get("/apikeys", response_model=APIKeyAnalyticsResponse)
async def analytics_for_apikeys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api_keys = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == current_user.id)
        .order_by(desc(APIKey.created_at))
    )

    total_keys = 0
    active_keys = 0
    key_rows = []
    for api_key in api_keys.scalars().all():
        total_keys += 1
        if api_key.is_active:
            active_keys += 1

        key_rows.append(
            {
                "id": api_key.id,
                "name": api_key.name,
                "is_active": api_key.is_active,
                "created_at": api_key.created_at,
            }
        )

    total_usage = await db.scalar(
        select(func.count(APIUsage.id)).where(APIUsage.user_id == current_user.id)
    )
    avg_latency = await db.scalar(
        select(func.avg(APIUsage.latency_ms)).where(APIUsage.user_id == current_user.id)
    )
    cache_hits = await db.scalar(
        select(func.count(APIUsage.id)).where(
            APIUsage.user_id == current_user.id,
            APIUsage.cached.is_(True),
        )
    )

    return {
        "total_keys": total_keys,
        "active_keys": active_keys,
        "total_requests": int(total_usage or 0),
        "average_latency_ms": round(avg_latency or 0, 2),
        "cache_hit_rate": round(
            ((cache_hits or 0) / total_usage * 100) if total_usage else 0, 2
        ),
        "keys": key_rows,
    }
