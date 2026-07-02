import secrets

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import APIKey, User
from app.routers.auth import get_current_user, get_password_hash
from app.schemas import APIKeyCreateResponse, APIKeyResponse

router = APIRouter(prefix="/apikeys", tags=["apikeys"])

def generate_apikey() -> str:
    return f"pk_live_{secrets.token_urlsafe(32)}"

@router.post("/create", response_model=APIKeyCreateResponse)
async def create_apikey(
    name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    raw_key = generate_apikey()
    hashed_key = get_password_hash(raw_key)

    api_key = APIKey(
        name=name,
        user_id=current_user.id,
        key_hash=hashed_key,
        is_active=True,
    )

    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return APIKeyCreateResponse(api_key=raw_key, message="Store securely")

@router.get("/", response_model=list[APIKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(APIKey).where(APIKey.user_id == current_user.id)
    )
    api_keys = result.scalars().all()
    return [APIKeyResponse.model_validate(api_key) for api_key in api_keys]

@router.delete("/{key_id}")
async def revoke_apikey(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    )
    
    api_key = result.scalars().first()
    if api_key:
        api_key.is_active = False
        await db.commit()
        return {"message": "API key revoked"}
    return {"message": "API key not found"}