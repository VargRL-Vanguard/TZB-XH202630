"""
基础配置（**不含**任何 *_DB_URL，数据库由各区自管）。
使用 pydantic-settings，自动从 .env 加载。
"""
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局基础配置。所有区共用，DB_URL 由各区自己的 config.py 加载。"""

    # 运行环境
    ENV: Literal["dev", "test", "prod"] = "dev"

    # 服务端口
    PORT: int = 8000

    # 日志级别
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # JWT 密钥（生产环境必须改）
    JWT_SECRET: str = "dev-secret-change-in-prod-2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    # Agent 超时（秒）
    AGENT_TIMEOUT_SEC: int = 30

    # 3 项硬指标阈值（夺奖硬指标）
    QUALITY_THRESHOLD_HALLUCINATION: float = 0.05      # < 5%
    QUALITY_THRESHOLD_MATCH_ACCURACY: float = 0.85     # ≥ 85%
    QUALITY_THRESHOLD_COVERAGE: float = 0.90           # ≥ 90%

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# 单例
settings = Settings()
