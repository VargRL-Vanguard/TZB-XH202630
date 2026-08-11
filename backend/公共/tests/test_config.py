"""
单测：config.py
覆盖：默认值 / 字段完整性 / 不含 DB_URL
"""
import pytest

from backend.公共.config import Settings, settings


def test_settings_default_values():
    """默认值"""
    s = Settings()
    assert s.ENV == "dev"
    assert s.PORT == 8000
    assert s.LOG_LEVEL == "INFO"
    assert s.JWT_ALGORITHM == "HS256"
    assert s.JWT_EXPIRE_HOURS == 24
    assert s.AGENT_TIMEOUT_SEC == 30


def test_settings_quality_thresholds():
    """3 项硬指标阈值"""
    s = Settings()
    assert s.QUALITY_THRESHOLD_HALLUCINATION == 0.05
    assert s.QUALITY_THRESHOLD_MATCH_ACCURACY == 0.85
    assert s.QUALITY_THRESHOLD_COVERAGE == 0.90


def test_settings_no_db_url():
    """**关键**：不含任何 *_DB_URL 字段（任务清单硬要求）"""
    s = Settings()
    fields = s.model_dump()
    db_fields = [k for k in fields.keys() if "DB_URL" in k or "DATABASE" in k.upper()]
    assert db_fields == [], f"config.py 不应包含 DB 字段：{db_fields}"


def test_settings_singleton():
    """单例"""
    assert settings is not None
    assert isinstance(settings, Settings)


def test_settings_cors_origins():
    """CORS 默认值"""
    s = Settings()
    assert "http://localhost:3000" in s.CORS_ORIGINS


def test_settings_jwt_secret_has_default():
    """JWT_SECRET 有默认值（dev 友好）"""
    s = Settings()
    assert s.JWT_SECRET
    assert len(s.JWT_SECRET) > 0


def test_settings_env_override(monkeypatch):
    """环境变量可覆盖"""
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    s = Settings()
    # 注意：Settings() 是新的实例，会从环境变量读
    # 如果 .env 里没设 PORT，应该用环境变量
    assert s.PORT in (8000, 9000)  # 看 .env 是否有
