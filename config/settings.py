from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "Py-Scaffold API"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/dbname"

    # CORS
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = False

    # Logging
    log_level: str = "INFO"


settings = Settings()
