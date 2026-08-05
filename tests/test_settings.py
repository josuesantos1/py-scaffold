"""Tests for config/settings.py — _parse() and defaults."""

from config.settings import Settings, _parse


def test_defaults():
    s = _parse({})
    assert s.cors_origins == ["*"]
    assert s.debug is False
    assert s.cors_allow_credentials is False
    assert s.log_level == "INFO"


def test_cors_origins_single_wildcard():
    s = _parse({"CORS_ORIGINS": "*"})
    assert s.cors_origins == ["*"]


def test_cors_origins_comma_separated():
    s = _parse({"CORS_ORIGINS": "http://a.com,http://b.com"})
    assert s.cors_origins == ["http://a.com", "http://b.com"]


def test_cors_origins_trims_whitespace():
    s = _parse({"CORS_ORIGINS": "  http://a.com  ,  http://b.com  "})
    assert s.cors_origins == ["http://a.com", "http://b.com"]


def test_debug_true_variants():
    for val in ("1", "true", "yes", "on", "True", "YES"):
        assert _parse({"DEBUG": val}).debug is True


def test_debug_false():
    assert _parse({"DEBUG": "false"}).debug is False
    assert _parse({"DEBUG": "0"}).debug is False


def test_log_level_uppercased():
    s = _parse({"LOG_LEVEL": "debug"})
    assert s.log_level == "DEBUG"


def test_database_url_override():
    url = "postgresql+asyncpg://u:p@host:5432/db"
    s = _parse({"DATABASE_URL": url})
    assert s.database_url == url


def test_cors_allow_credentials():
    assert _parse({"CORS_ALLOW_CREDENTIALS": "true"}).cors_allow_credentials is True
    assert _parse({"CORS_ALLOW_CREDENTIALS": "false"}).cors_allow_credentials is False


def test_settings_is_frozen():
    s = Settings()
    try:
        s.debug = True  # type: ignore[misc]
        raise AssertionError("Should have raised")
    except (AttributeError, TypeError):
        pass
