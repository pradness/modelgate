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

class UserLogin(BaseModel):
    email: str
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

class TokenResponse(Token):
    pass

class APIKeyResponse(BaseModel):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class APIKeyCreateResponse(BaseModel):
    api_key: str
    message: str

class ModelBase(BaseModel):
    name: str
    version: str
    endpoint: str

class ModelCreate(ModelBase):
    pass

class ModelUpdate(BaseModel):
    endpoint: str | None = None
    status: bool | None = None

class ModelResponse(ModelBase):
    id: int
    status: bool
    created_at: datetime

    class Config:
        from_attributes = True