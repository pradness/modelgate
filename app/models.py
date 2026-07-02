# Define what your PostgreSQL tables look like.

from sqlalchemy import Integer, String, Boolean, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from sqlalchemy.orm import relationship

# One to one copy of the User model.
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    api_keys = relationship("APIKey", back_populates="user")
    usage_logs = relationship("APIUsage", back_populates="user")    

# API key model.
class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    key_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="api_keys")

class ModelRegistry(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    endpoint: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    usage_logs = relationship("APIUsage", back_populates="model")

class APIUsage(Base):
    __tablename__ = "api_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    latency_ms: Mapped[float]
    status_code: Mapped[int]
    cached: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="usage_logs")
    model = relationship("ModelRegisty", back_populates="usage_logs")