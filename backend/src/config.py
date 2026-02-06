from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global application settings."""

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    APP_VERSION: str = "0.1.0"

    model_config = {"env_prefix": "APP_", "extra": "ignore"}


settings = Settings()
