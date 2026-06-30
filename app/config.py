# Use pydantic-settings (or standard os.environ) to load variables safely.

import os
from dotenv import load_dotenv, find_dotenv
from pydantic_settings import BaseSettings
load_dotenv(find_dotenv())
# Settings class for loading environment variables.
class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://dbuser:1729@localhost:5432/fastapi")

settings = Settings()