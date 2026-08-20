"""
Centralized Configuration & Settings for WorkVision AI.
"""

import json
from functools import lru_cache
from typing import List, Union
from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --------------------------------------------------------------------------
    # 1. App General & Environment
    # --------------------------------------------------------------------------
    APP_NAME: str = "WorkVision AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    TIMEZONE: str = "Asia/Jakarta"

    # --------------------------------------------------------------------------
    # 2. Database PostgreSQL
    # --------------------------------------------------------------------------
    POSTGRES_USER: str = "workvision"
    POSTGRES_PASSWORD: str = "workvision_secret_2026"
    POSTGRES_DB: str = "workvision_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    DATABASE_URL: str = (
        "postgresql+asyncpg://workvision:workvision_secret_2026@localhost:5432/workvision_db"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # --------------------------------------------------------------------------
    # 3. Redis Broker & Streams
    # --------------------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"
    STREAM_VISION_EVENTS: str = "stream:vision:events"
    STREAM_ATTENDANCE_EVENTS: str = "stream:attendance:events"
    STREAM_SYSTEM_HEALTH: str = "stream:system:health"

    # --------------------------------------------------------------------------
    # 4. Vision Worker & AI Inference
    # --------------------------------------------------------------------------
    YOLO_MODEL_PATH: str = "models/detection/yolov8n.pt"
    INFERENCE_DEVICE: str = "cuda:0"  # 'cuda:0' or 'cpu'
    CONFIDENCE_THRESHOLD: float = 0.50
    IOU_THRESHOLD: float = 0.45
    INFERENCE_FPS: int = 10
    MAX_FRAME_QUEUE_SIZE: int = 1  # Drop-oldest queue policy

    # --------------------------------------------------------------------------
    # 5. ByteTrack Tracking Parameters
    # --------------------------------------------------------------------------
    TRACK_HIGH_THRESH: float = 0.60
    TRACK_LOW_THRESH: float = 0.10
    NEW_TRACK_THRESH: float = 0.70
    MATCH_THRESH: float = 0.80
    TRACK_BUFFER: int = 30

    # --------------------------------------------------------------------------
    # 6. Temporal State Machine
    # --------------------------------------------------------------------------
    STATE_DEBOUNCE_SECONDS: int = 30
    AWAY_TIMEOUT_SECONDS: int = 300
    BREAK_MIN_SECONDS: int = 180
    MEETING_MIN_SECONDS: int = 120

    # --------------------------------------------------------------------------
    # 7. Security, Encryption & UU PDP
    # --------------------------------------------------------------------------
    BIOMETRIC_ENCRYPTION_KEY: str = (
        "workvision_biometric_aes256_super_secret_key_change_in_production_32chars!"
    )
    JWT_SECRET_KEY: str = "workvision_jwt_secret_change_in_production_key_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # --------------------------------------------------------------------------
    # 8. API & WebSocket Gateway
    # --------------------------------------------------------------------------
    HOST: str = Field(
        default="0.0.0.0",
        validation_alias=AliasChoices("HOST", "API_HOST"),
        description="Host interface to bind API server",
    )
    PORT: int = Field(
        default=8000,
        validation_alias=AliasChoices("PORT", "API_PORT"),
        description="Port to bind API server",
    )
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @property
    def API_HOST(self) -> str:
        return self.HOST

    @property
    def API_PORT(self) -> int:
        return self.PORT

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            try:
                return json.loads(v)
            except Exception:
                return [v]
        elif isinstance(v, list):
            return v
        return []

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
