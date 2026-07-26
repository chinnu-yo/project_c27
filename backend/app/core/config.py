import os
import logging
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

logger = logging.getLogger(__name__)

# Base64 url-safe 32-byte key for local dev fallback
DEV_FERNET_KEY = "uP9Q-nK8m1J4v7x2z5A8b3C6d9E2f5G8h1I4j7K0l3M="

class Settings(BaseModel):
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        alias="MONGODB_URI"
    )
    gemini_api_key: str = Field(
        default="",
        alias="GEMINI_API_KEY"
    )
    port: int = Field(
        default=8000,
        alias="PORT"
    )
    env: str = Field(
        default="development",
        alias="ENV"
    )
    jwt_secret: str = Field(
        default="placeholder_secret_key",
        alias="JWT_SECRET"
    )
    encryption_key: str = Field(
        default="",
        alias="ENCRYPTION_KEY"
    )

    class Config:
        populate_by_name = True

_env = os.getenv("ENV", "development").lower()
_jwt_secret = os.getenv("JWT_SECRET", "placeholder_secret_key")
_encryption_key = os.getenv("ENCRYPTION_KEY", "")

if _env == "production":
    if not _jwt_secret or _jwt_secret == "placeholder_secret_key":
        raise ValueError("CRITICAL SECURITY ERROR: JWT_SECRET must be explicitly configured in production environment!")
    if not _encryption_key:
        raise ValueError("CRITICAL SECURITY ERROR: ENCRYPTION_KEY must be explicitly configured in production environment!")
else:
    if not _jwt_secret or _jwt_secret == "placeholder_secret_key":
        logger.warning("SECURITY WARNING: Using default placeholder JWT_SECRET in development mode.")
    if not _encryption_key:
        logger.warning("SECURITY WARNING: Using default development ENCRYPTION_KEY. Do NOT use in production!")
        _encryption_key = DEV_FERNET_KEY

# Load and instantiate settings using environment variables
settings = Settings(
    MONGODB_URI=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
    GEMINI_API_KEY=os.getenv("GEMINI_API_KEY", ""),
    PORT=int(os.getenv("PORT", "8000")),
    ENV=_env,
    JWT_SECRET=_jwt_secret,
    ENCRYPTION_KEY=_encryption_key
)

