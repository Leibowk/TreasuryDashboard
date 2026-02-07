from pydantic_settings import BaseSettings


# Standard treasury curve terms (display order) and FRED series IDs
TERM_TO_SERIES_ID: dict[str, str] = {
    "1M": "DGS1MO",
    "3M": "DGS3MO",
    "6M": "DGS6MO",
    "1Y": "DGS1",
    "2Y": "DGS2",
    "5Y": "DGS5",
    "10Y": "DGS10",
    "30Y": "DGS30",
}


class Settings(BaseSettings):
    """Global application settings."""

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    APP_VERSION: str = "0.1.0"
    FRED_API_KEY: str
    FRED_BASE_URL: str = "https://api.stlouisfed.org"
    DATABASE_URL: str = "sqlite:///./treasury.db"

    model_config = {
        "env_prefix": "APP_",
        "extra": "ignore",
        "env_file": ".env",
    }


settings = Settings()
