"""
Token 黑名单（登出后失效）。

**当前实现**：进程级 set（重启失效，**仅适合单进程演示**）。
**生产建议**：换 Redis，key=`blacklist:token:<jwt>`, value=1, TTL=exp - now。

**为什么不存数据库**：JWT 设计本身是无状态的，登出只是为了"立刻失效已签发的 token"，
                  在 Redis 里加 TTL 即可，到期自动清，**不需要**写入业务表。
"""
import threading
from typing import Set

# 进程级 set（threading.Lock 保护并发写）
_lock = threading.Lock()
_blacklist: Set[str] = set()


def add_to_blacklist(token: str) -> None:
    """把 token 加入黑名单。"""
    with _lock:
        _blacklist.add(token)


def is_blacklisted(token: str) -> bool:
    """检查 token 是否在黑名单。"""
    with _lock:
        return token in _blacklist


def clear_blacklist() -> None:
    """测试用：清空黑名单。生产不要调用。"""
    global _blacklist
    with _lock:
        _blacklist.clear()
