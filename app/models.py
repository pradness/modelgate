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

    api_keys = relationship("APIKey", back_populates="user")

# API key model.
class APIKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    key_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user = relationship("User", back_populates="api_keys")