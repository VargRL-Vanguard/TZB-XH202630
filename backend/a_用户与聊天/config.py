"""
A 区自有配置：USER_CHAT_DB_URL（**不**与 公共/ 共享）。

约定：
- A 区的数据库连接信息**只**通过环境变量 / .env 加载
- B / C / D 各管自己的 *_DB_URL，**禁止**读这个配置
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class AConfig(BaseSettings):
    """A 区（用户与聊天）配置。"""

    # 数据库连接 URL（必填）
    # 格式：mysql+aiomysql://user:password@host:port/dbname
    USER_CHAT_DB_URL: str = (
        "mysql+aiomysql://root:password@localhost:3306/tzb_user_chat"
    )

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
a_config = AConfig()
