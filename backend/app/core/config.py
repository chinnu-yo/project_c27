import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

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

    class Config:
        populate_by_name = True

# Load and instantiate settings using environment variables
settings = Settings(
    MONGODB_URI=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
    GEMINI_API_KEY=os.getenv("GEMINI_API_KEY", ""),
    PORT=int(os.getenv("PORT", "8000")),
    ENV=os.getenv("ENV", "development"),
    JWT_SECRET=os.getenv("JWT_SECRET", "placeholder_secret_key")
)
