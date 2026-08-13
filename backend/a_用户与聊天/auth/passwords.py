"""
密码哈希 + 强度校验。

**规则**（A-01 验收标准）：
- bcrypt 哈希（passlib）
- 密码强度：≥ 8 位 + 至少 1 个字母 + 至少 1 个数字
- 强度不达标 → BizError 400 "密码强度不足"
"""
import re
from passlib.context import CryptContext

from backend.公共.errors import BizError


# bcrypt 上下文（自动处理 salt + cost factor）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """
    把明文密码哈希成 bcrypt。
    :return: $2b$12$... 这种字符串（60 字符）
    """
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    验证明文 vs 哈希。
    :return: True 匹配 / False 不匹配
    """
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        # 哈希格式错误等情况
        return False


# 强度校验正则
_HAS_LETTER = re.compile(r"[A-Za-z]")
_HAS_DIGIT = re.compile(r"\d")


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    校验密码强度。
    :return: (True, "") 合格 / (False, "原因") 不合格
    """
    if len(password) < 8:
        return False, "密码长度至少 8 位"
    if not _HAS_LETTER.search(password):
        return False, "密码必须包含至少 1 个字母"
    if not _HAS_DIGIT.search(password):
        return False, "密码必须包含至少 1 个数字"
    return True, ""


def ensure_strong_password(password: str) -> None:
    """业务调用方用：强度不够直接抛 BizError。"""
    ok, reason = validate_password_strength(password)
    if not ok:
        raise BizError(f"密码强度不足：{reason}", code=400)
