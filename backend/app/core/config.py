from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # App
    APP_NAME: str = "SE_ARIES"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # API
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./se_aries.db"

    # Security
    SECRET_KEY: str = "change-this-in-production-super-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Data defaults
    DEFAULT_DISCOUNT_RATE: float = 10.0
    DEFAULT_CURRENCY: str = "USD"
    DEFAULT_VOLUME_UNIT: str = "BBL"  # BBL or MCF

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
