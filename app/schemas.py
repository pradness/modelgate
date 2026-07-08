# Define how data should look when it enters or leaves your API using Pydantic models.

from datetime import datetime
from typing import Any

from pydantic import BaseModel

# ----------------------------------------------USER


class UserBase(BaseModel):
    username: str
    role: str


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime | None = None

    class Config:
        from_attributes = True


# ---------------------------------------------TOKEN


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class TokenResponse(Token):
    pass


# --------------------------------------------APIKEY


class APIKeyResponse(BaseModel):
    id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    api_key: str
    message: str


# ---------------------------------------------MODEL


class ModelBase(BaseModel):
    name: str
    description: str | None = None
    task: str


class ModelCreate(ModelBase):
    pass


class ModelUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    task: str | None = None


class ModelResponse(ModelBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


# --------------------------------------MODELVERSION


class ModelVersionBase(BaseModel):
    version: str
    service_url: str
    artifact_uri: str


class ModelVersionCreate(ModelVersionBase):
    pass


class ModelVersionUpdate(BaseModel):
    version: str | None = None
    service_url: str | None = None
    artifact_uri: str | None = None
    status: str | None = None


class ModelVersionResponse(ModelVersionBase):
    id: int
    model_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModelDetailResponse(ModelResponse):
    versions: list[ModelVersionResponse]


# ----------------------------------------PREDICTION


class PredictionRequest(BaseModel):
    input: Any


class PredictionResponse(BaseModel):
    prediction: Any
    version: str
    cached: bool
    latency_ms: float


# ---------------------------------------------USAGE


class UsageResponse(BaseModel):
    id: int
    user_id: int
    model_version_id: int
    latency_ms: float
    status_code: int
    cached: bool
    created_at: datetime

    class Config:
        from_attributes = True


# -----------------------------------------ANALYTICS


class ModelUsageStats(BaseModel):
    model: str
    requests: int
    average_latency_ms: float


class LatencyStats(BaseModel):
    average_latency_ms: float
    p95_latency_ms: float
    cache_hit_rate: float


class TopModels(BaseModel):
    model: str
    requests: int


# -----------------------------------------ANALYTICS RESPONSES


class VersionAnalyticsItem(BaseModel):
    version: str
    status: str
    requests: int
    average_latency_ms: float
    cache_hit_rate: float


class ModelVersionsAnalyticsResponse(BaseModel):
    model: str
    versions: list[VersionAnalyticsItem]


class APIKeyAnalyticsItem(BaseModel):
    id: int
    name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyAnalyticsResponse(BaseModel):
    total_keys: int
    active_keys: int
    total_requests: int
    average_latency_ms: float
    cache_hit_rate: float
    keys: list[APIKeyAnalyticsItem]
