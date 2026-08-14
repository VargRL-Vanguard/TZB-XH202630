"""
D 区自有配置：AI_INTEGRATION_DB_URL + 3+1 个 AI 的 key/endpoint。

约定：
- D 区的数据库连接信息只通过环境变量 / .env 加载
- A / B / C 各管自己的 *_DB_URL，禁止读这个配置
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class DConfig(BaseSettings):
    """D 区（AI 集成）配置。"""

    # AI 集成主库连接 URL（必填）
    AI_INTEGRATION_DB_URL: str = (
        "sqlite+aiosqlite:///./backend/d_AI集成/tzb_ai_integration.db"
    )

    # ---- 3 个 AI 服务配置 ----
    # ChatAI（辅导对话）
    CHAT_AI_API_KEY: str = ""
    CHAT_AI_ENDPOINT: str = ""
    CHAT_AI_MODEL: str = "gpt-4o-mini"

    # PathAI（学习路径生成）
    PATH_AI_API_KEY: str = ""
    PATH_AI_ENDPOINT: str = ""
    PATH_AI_MODEL: str = "gpt-4o-mini"

    # SuggestAI（学习建议生成）
    SUGGEST_AI_API_KEY: str = ""
    SUGGEST_AI_ENDPOINT: str = ""
    SUGGEST_AI_MODEL: str = "gpt-4o-mini"

    # EmbedAI（知识库 embedding 检索）
    EMBED_AI_API_KEY: str = ""
    EMBED_AI_ENDPOINT: str = ""
    EMBED_AI_MODEL: str = "text-embedding-3-small"

    # 引擎调试选项
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 3600

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


d_config = DConfig()