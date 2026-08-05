"""Application settings loaded from environment variables."""

import os
from pathlib import Path

import msgspec


class Settings(msgspec.Struct, frozen=True):
    app_name: str = "Py-Scaffold API"
    app_version: str = "0.1.0"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/dbname"
    cors_origins: list[str] = msgspec.field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = False
    log_level: str = "INFO"


def _load_dotenv(path: str = ".env") -> None:
    p = Path(path)
    if not p.is_file():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        val = val.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), val)


def _parse(env: dict[str, str]) -> Settings:
    data: dict[str, object] = {}

    if v := env.get("APP_NAME"):
        data["app_name"] = v
    if v := env.get("APP_VERSION"):
        data["app_version"] = v
    if v := env.get("DEBUG"):
        data["debug"] = v.lower() in ("1", "true", "yes", "on")
    if v := env.get("DATABASE_URL"):
        data["database_url"] = v
    if v := env.get("CORS_ORIGINS"):
        data["cors_origins"] = [o.strip() for o in v.split(",") if o.strip()]
    if v := env.get("CORS_ALLOW_CREDENTIALS"):
        data["cors_allow_credentials"] = v.lower() in ("1", "true", "yes", "on")
    if v := env.get("LOG_LEVEL"):
        data["log_level"] = v.upper()

    return msgspec.convert(data, Settings)


def _load_settings() -> Settings:
    _load_dotenv()
    return _parse(dict(os.environ))


settings = _load_settings()
