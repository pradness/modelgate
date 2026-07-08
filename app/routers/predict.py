import json
from time import perf_counter

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.model_queries import (
    get_api_key_by_value,
    get_latest_model_version,
    get_model_version,
    get_owned_model_by_name,
    record_api_usage,
)
from app.routers.auth import get_current_user
from app.schemas import PredictionRequest, PredictionResponse

router = APIRouter(prefix="/predict", tags=["predict"], dependencies=[Depends(get_current_user)])


def _extract_cached(body_text: str, headers: dict[str, str]) -> bool:
    try:
        body = json.loads(body_text)
        if isinstance(body, dict) and isinstance(body.get("cached"), bool):
            return body["cached"]
    except json.JSONDecodeError:
        pass

    cache_header = headers.get("x-cache") or headers.get("X-Cache")
    if cache_header is not None:
        return cache_header.lower() in {"hit", "true", "1", "cached"}

    return False


def _extract_prediction(body_text: str):
    try:
        return json.loads(body_text)
    except json.JSONDecodeError:
        return body_text


async def _send_upstream_request(
    url: str, payload: dict
) -> tuple[int, dict[str, str], str]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload)
        return response.status_code, dict(response.headers), response.text


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

    started_at = perf_counter()

    try:
        status_code, headers, body_text = await _send_upstream_request(
            model_version.service_url,
            request.model_dump(),
        )
        cached = _extract_cached(body_text, headers)
        latency_ms = (perf_counter() - started_at) * 1000
        prediction = _extract_prediction(body_text)

        await record_api_usage(
            db=db,
            user_id=api_key_record.user_id,
            model_version_id=model_version.id,
            latency_ms=latency_ms,
            status_code=status_code,
            cached=cached,
        )

        if status_code >= 400:
            raise HTTPException(status_code=status_code, detail=prediction)

        return PredictionResponse(
            prediction=prediction,
            version=model_version.version,
            cached=cached,
            latency_ms=latency_ms,
        )

    except httpx.RequestError as exc:
        latency_ms = (perf_counter() - started_at) * 1000
        await record_api_usage(
            db=db,
            user_id=api_key_record.user_id,
            model_version_id=model_version.id,
            latency_ms=latency_ms,
            status_code=status.HTTP_502_BAD_GATEWAY,
            cached=False,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to reach model service: {exc}",
        )
