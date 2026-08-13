"""
B 区自有配置：STUDENT_DATA_DB_URL + KB_VECTOR_DB_URL。

约定：
- B 区的数据库连接信息只通过环境变量 / .env 加载
- A / C / D 各管自己的 *_DB_URL，禁止读这个配置
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class BConfig(BaseSettings):
    """B 区（学情数据）配置。"""

    # 学情数据主库连接 URL（必填）
    # 格式：mysql+aiomysql://user:password@host:port/dbname
    # 测试环境可使用 sqlite+aiosqlite 避免外部依赖
    STUDENT_DATA_DB_URL: str = (
        "sqlite+aiosqlite:///./backend/b_学情数据/tzb_student_data.db"
    )

    # 向量库 URL（如使用 pgvector / Chroma / Faiss）
    # MVP 阶段先不用，embedding 以 JSON 形式存主库
    KB_VECTOR_DB_URL: str = ""

    # 引擎调试选项
    DB_ECHO: bool = False  # True 时打印所有 SQL（生产必须 False）
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 3600  # 1 小时回收连接，避开 MySQL 8h 默认断开

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# 单例
b_config = BConfig()
