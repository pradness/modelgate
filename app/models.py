# Define what your PostgreSQL tables look like.

from enum import Enum

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import CheckConstraint

from app.database import Base


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class TaskType(str, Enum):
    TEXT_GENERATION = "text_generation"

class ModelStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"

# One to one copy of the User model.
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, nullable=False, autoincrement=True
    )
    username: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role_enum"), nullable=False
    )
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )

    api_keys = relationship("APIKey", back_populates="user")
    usage_logs = relationship("APIUsage", back_populates="user")
    models = relationship("ModelRegistry", back_populates="owner")


# API key model.
class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, nullable=False, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    key_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="api_keys")
    usage_logs = relationship("APIUsage", back_populates="api_key")


class ModelRegistry(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, nullable=False, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    task: Mapped[TaskType] = mapped_column(
        SAEnum(TaskType, name="task_type_enum"), nullable=False
    )
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )

    versions = relationship("ModelVersions", back_populates="model")
    owner = relationship("User", back_populates="models")


class ModelVersions(Base):
    __tablename__ = "model_versions"
    __table_args__ = (
        UniqueConstraint("model_id", "version", name="uq_model_version_per_model"),
        CheckConstraint("length(service_url) > 0", name="service_url not empty"),
        CheckConstraint("length(artifact_uri) > 0", name="artifact_uri not empty")
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, nullable=False, autoincrement=True
    )
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    service_url: Mapped[str] = mapped_column(String, nullable=False)
    artifact_uri: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(SAEnum(ModelStatus), nullable=False, default=ModelStatus.ACTIVE)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )

    model = relationship("ModelRegistry", back_populates="versions")
    usage_logs = relationship("APIUsage", back_populates="model_version")


class APIUsage(Base):
    __tablename__ = "api_usage"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, nullable=False, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    api_key_id: Mapped[int] = mapped_column(ForeignKey("api_keys.id"), nullable=False)
    model_version_id: Mapped[int] = mapped_column(
        ForeignKey("model_versions.id"), nullable=False
    )
    latency_ms: Mapped[float]
    status_code: Mapped[int]
    cached: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="usage_logs")
    api_key = relationship("APIKey", back_populates="usage_logs")
    model_version = relationship("ModelVersions", back_populates="usage_logs")
