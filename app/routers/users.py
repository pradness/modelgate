# users
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse
from app.routers.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/health")
async def users_health():
    return {"message": "users router works"}\

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/{id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(id: int, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.id==id))
    if not user:
        raise HTTPException(detail="user not found", status_code=status.HTTP_404_NOT_FOUND)
    return user

@router.patch("/{id}", response_model=UserResponse)
async def update_user(id: int, payload: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.id==id))
    if not user:
        raise HTTPException(detail="user not found", status_code=status.HTTP_404_NOT_FOUND)
    user.email = payload.email
    user.password_hash = payload.password
    user.role = payload.role
    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(id: int, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.id==id))
    if not user:
        raise HTTPException(detail="user not found", status_code=status.HTTP_404_NOT_FOUND)
    await db.delete(user)
    await db.commit()
    return None