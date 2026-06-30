# auth
from datetime import datetime, timedelta
import os

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, Token

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_h = PasswordHash.recommended()
# DUMMY_HASH = password_h.hash("dummypassword")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

router = APIRouter(prefix="/auth", tags=["auth"])

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_h.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return password_h.hash(password)

async def get_user(db: AsyncSession, email: str) -> User | None:

    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def authenticate_user(
    db: AsyncSession, 
    email: str, 
    password: str
) -> User | None:

    user = await get_user(db, email)

    if not user or not verify_password(password, user.password_hash):
        return None

    return user

def create_access_token(
    data: dict, 
    expires_delta: timedelta | None = None
) -> str:

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        SECRET_KEY, 
        algorithm=ALGORITHM
    )

    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
) -> User:

    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Could not validate credentials"
    )

    try:

        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        email: str = payload.get("sub")  # type: ignore

        if email is None:
            raise credential_exception

    except InvalidTokenError:
        raise credential_exception

    user = await get_user(db, email)
    if user is None:
        raise credential_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    return current_user

@router.post("/register", response_model=UserResponse)
async def register(
    user: UserCreate, 
    db: AsyncSession = Depends(get_db)
) -> UserResponse:

    hashed_password = get_password_hash(user.password)

    db_user = User(
        email=user.email, 
        password_hash=hashed_password, 
        role=user.role
    )

    existing_user = await get_user(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return UserResponse.model_validate(db_user)

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
) -> Token:

    db_user = await authenticate_user(
        db, form_data.username, 
        form_data.password
    )

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect email or password"
        )
        
    access_token = create_access_token(data={"sub": db_user.email})

    return Token(access_token=access_token, token_type="bearer")
