"""Application Configuration Management"""
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/dbname"
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Agent Backend"
    DEBUG: bool = False
    
    # Security
    API_KEY: str = "change-me-in-production"
    SECRET_KEY: str = "change-me-in-production"
    
    # Agent Configuration
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT: int = 300
    
    # LLM Configuration
    LLM_PROVIDER: str = ""
    GEMINI_API_KEY: str = ""
    LLM_API_KEY: str | None = None
    LLM_MODEL: str = ""
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Phase 2: Security Hardening
    
    # Encryption
    ENCRYPTION_KEY: str | None = None
    
    # Device Fingerprinting
    FINGERPRINT_MATCH_THRESHOLD: float = 0.7
    FINGERPRINT_STRICT_MODE: bool = False
    
    # Rate Limiting
    RATE_LIMIT_RPM: int = 60
    RATE_LIMIT_RPH: int = 1000
    RATE_LIMIT_ENABLED: bool = True
    
    # Security Event Logging
    SECURITY_LOG_EVENTS: bool = True
    AUTO_BLOCK_SUSPICIOUS_USERS: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def assemble_db_connection(cls, v: str | None) -> str:
        if isinstance(v, str):
            if v.startswith("postgresql://"):
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
            v = v.replace("sslmode=", "ssl=")
            v = v.replace("&channel_binding=require", "").replace("channel_binding=require", "")
        return v

    @field_validator("GEMINI_API_KEY")
    @classmethod
    def set_gemini_key(cls, v: str, info) -> str:
        # If GEMINI_API_KEY is empty, try to use LLM_API_KEY from values
        if not v and info.data.get("LLM_API_KEY"):
            return info.data["LLM_API_KEY"]
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
