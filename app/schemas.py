# Define how data should look when it enters or leaves your API using Pydantic models.

from datetime import datetime
from pydantic import BaseModel

# Base schema for user data.
class UserBase(BaseModel):
    email: str
    role: str

# Schema for creating a user.
class UserCreate(UserBase):
    password: str

# Schema for returning user data.
class UserResponse(UserBase):
    id: int
    created_at: datetime | None = None

    class Config:
        from_attributes = True

# Schema for token.
class Token(BaseModel):
    access_token: str
    token_type: str

# Schema for token data.
class TokenData(BaseModel):
    username: str | None = None

# Schema for returning model data.
class Model(BaseModel):
    id: str
    name: str
    description: str
    active_version_id: str

# Schema for returning API usage data.
class ApiUsage(BaseModel):
    user: str
    model: str
    latency_ms: float
    timestamp: datetime

# Schema for returning model registry data.
class ModelRegistry(BaseModel):
    model_name: str
    version: str
    endpoint: str
    status: str

# Schema for making a prediction request.
class PredictionRequest(BaseModel):
    id: str
    user_id: str
    model_version_id: str
    input_data: dict
    output_data: dict
    latency_ms: float
    cache_hit: bool

# Schema for returning prediction results.
class PredictionResponse(BaseModel):
    id: str
    user_id: str
    model_version_id: str
    output_data: dict
    latency_ms: float
    cache_hit: bool
