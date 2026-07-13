from config.settings import Settings


def test_cors_origins_single_wildcard():
    s = Settings(cors_origins="*")  # type: ignore[arg-type]
    assert s.cors_origins == ["*"]


def test_cors_origins_comma_separated():
    s = Settings(cors_origins="http://a.com, http://b.com")  # type: ignore[arg-type]
    assert s.cors_origins == ["http://a.com", "http://b.com"]


def test_cors_origins_trims_whitespace():
    s = Settings(cors_origins="  http://a.com  ,  http://b.com  ")  # type: ignore[arg-type]
    assert s.cors_origins == ["http://a.com", "http://b.com"]


def test_cors_origins_list_passthrough():
    s = Settings(cors_origins=["http://a.com"])
    assert s.cors_origins == ["http://a.com"]


def test_cors_origins_default():
    s = Settings()
    assert s.cors_origins == ["*"]
