from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "HILT - Human-in-the-Loop LLM"
    VERSION: str = "0.1.0"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # API Keys for LLM clients
    HILT_API_KEYS: str  # Comma-separated list

    # Initial operator credentials
    OPERATOR_USERNAME: str = "admin"
    OPERATOR_PASSWORD_HASH: str  # Bcrypt hash

    # Request timeout
    REQUEST_TIMEOUT_SECONDS: int = 300  # 5 minutes

    # CORS (comma-separated string)
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def api_keys_list(self) -> List[str]:
        """Parse comma-separated API keys into a list"""
        return [key.strip() for key in self.HILT_API_KEYS.split(",") if key.strip()]

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


# Global settings instance
settings = Settings()
