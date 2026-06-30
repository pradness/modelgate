# This holds your async connection factory and your base model layer.

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# Async engine is a proxy for the sync engine which allows asyncio to use the sync engine's connection pool.
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Async session local is a factory for creating async sessions.
async_session_local = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Base is the base class for all models.
class Base(DeclarativeBase):
    pass

async def get_db():
    # Dependency for getting a database session.
    async with async_session_local() as session:
        yield session