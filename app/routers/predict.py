import json
from time import perf_counter

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas import PredictionRequest, PredictionResponse
from app.services.cache import get_prediction, make_cache_key, store_prediction
from app.services.rate_limit import check_rate_limit
from app.services.model_queries import (
    get_api_key_by_value,
    get_latest_model_version,
    get_model_version,
    get_owned_model_by_name,
    record_api_usage,
)

router = APIRouter(
    prefix="/predict", tags=["predict"], dependencies=[Depends(get_current_user)]
)


async def _send_upstream_request(
    url: str, payload: dict
) -> tuple[int, dict[str, str], str]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload)
        return response.status_code, dict(response.headers), response.text


def _extract_prediction(body_text: str):
    try:
        return json.loads(body_text)
    except json.JSONDecodeError:
        return body_text


@router.post("/{model_name}", response_model=PredictionResponse)
async def predict(
    model_name: str,
    request: PredictionRequest,
    version: str | None = Query(default=None),
    api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    api_key_record = await get_api_key_by_value(db, api_key)
    if api_key_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    await check_rate_limit(api_key_record.id)
    
    model = await get_owned_model_by_name(db, model_name, api_key_record.user_id)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
        )

    if version is None:
        model_version = await get_latest_model_version(db, model.id)
    else:
        model_version = await get_model_version(db, model.id, version)

    if model_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Model version not found"
        )

    cache_key = make_cache_key(model.name, model_version.version, request.model_dump())
    started_at = perf_counter()

    cached_prediction = await get_prediction(cache_key)
    if cached_prediction is not None:
        latency_ms = (perf_counter() - started_at) * 1000
        await record_api_usage(
            db=db,
            user_id=api_key_record.user_id,
            api_key_id=api_key_record.id,
            model_version_id=model_version.id,
            latency_ms=latency_ms,
            status_code=status.HTTP_200_OK,
            cached=True,
        )
        return PredictionResponse(
            prediction=cached_prediction,
            version=model_version.version,
            cached=True,
            latency_ms=latency_ms,
        )

    try:
        status_code, _headers, body_text = await _send_upstream_request(
            model_version.service_url,
            request.model_dump(),
        )
        latency_ms = (perf_counter() - started_at) * 1000
        prediction = _extract_prediction(body_text)

        await record_api_usage(
            db=db,
            user_id=api_key_record.user_id,
            api_key_id=api_key_record.id,
            model_version_id=model_version.id,
            latency_ms=latency_ms,
            status_code=status_code,
            cached=False,
        )

        if status_code < 200 or status_code >= 300:
            raise HTTPException(status_code=status_code, detail=prediction)

        await store_prediction(cache_key, prediction)

        return PredictionResponse(
            prediction=prediction,
            version=model_version.version,
            cached=False,
            latency_ms=latency_ms,
        )

    except httpx.RequestError as exc:
        latency_ms = (perf_counter() - started_at) * 1000
        await record_api_usage(
            db=db,
            user_id=api_key_record.user_id,
            api_key_id=api_key_record.id,
            model_version_id=model_version.id,
            latency_ms=latency_ms,
            status_code=status.HTTP_502_BAD_GATEWAY,
            cached=False,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to reach model service: {exc}",
        )
