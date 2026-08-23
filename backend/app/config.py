"""
Central place to read environment variables.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:swetha@localhost:5432/justiceflow"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"
    cors_origins: str = "http://localhost:5173,http://localhost:5174"
    jwt_secret_key: str = "justiceflow_core_jwt_secret_key_2026_super_secure"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    class Config:
        env_file = ".env"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
