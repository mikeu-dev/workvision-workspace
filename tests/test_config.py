"""
Unit Tests for Centralized Configuration (workvision-config).
"""

from workvision_config import Settings, get_settings


def test_settings_default_values(settings: Settings):
    """Test default values of application settings."""
    assert settings.APP_NAME == "WorkVision AI"
    assert settings.DATABASE_POOL_SIZE == 20
    assert settings.DATABASE_MAX_OVERFLOW == 10
    assert "workvision_db" in settings.DATABASE_URL
    assert settings.STREAM_VISION_EVENTS == "stream:vision:events"
    assert settings.STATE_DEBOUNCE_SECONDS == 30


def test_cors_origins_parsing():
    """Test CORS origins validator parses list and json strings correctly."""
    # List format
    s1 = Settings(CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"])
    assert len(s1.CORS_ORIGINS) == 2
    assert "http://localhost:3000" in s1.CORS_ORIGINS

    # Comma-separated string format
    s2 = Settings(CORS_ORIGINS="http://localhost:3000, http://localhost:8080")
    assert len(s2.CORS_ORIGINS) == 2
    assert "http://localhost:8080" in s2.CORS_ORIGINS

    # JSON array string format
    s3 = Settings(CORS_ORIGINS='["http://example.com"]')
    assert s3.CORS_ORIGINS == ["http://example.com"]
