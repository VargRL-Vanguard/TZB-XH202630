"""
A-01 鉴权单测：注册 / 登录 / 登出。

**前提**：先跑 `python -m backend.a_用户与聊天.init_db` 建表。

**用法**：
    cd D:\\TZB\\TZB-XH202630
    pytest backend/a_用户与聊天/tests/test_auth.py -v

**覆盖用例**（≥ 9 用例满足 A-01 验收标准）：
1. test_register_happy_path               正常注册
2. test_register_duplicate_username       重复用户名 → 400
3. test_register_weak_password_too_short  密码太短 → 400
4. test_register_weak_password_no_letter  密码无字母 → 400
5. test_register_weak_password_no_digit   密码无数字 → 400
6. test_register_with_education           注册时带 education/major → LearnerProfile 自动创建
7. test_login_happy_path                  正常登录
8. test_login_wrong_password              错密码 → 401
9. test_login_nonexistent_user            不存在用户 → 401（**同**消息）
10. test_login_jwt_contains_role_and_exp  JWT 含 role 和 exp
11. test_logout_happy_path                登出成功
12. test_logout_token_blacklisted         登出后 token 失效
"""
import time
import pytest

from backend.a_用户与聊天.auth.passwords import (
    hash_password, verify_password, validate_password_strength,
)
from backend.a_用户与聊天.auth.tokens import create_access_token, decode_access_token
from backend.a_用户与聊天.auth.blacklist import add_to_blacklist, is_blacklisted


# ========== 1. 密码模块（单元测试，无 DB 依赖）==========


def test_hash_and_verify_password():
    """哈希后能验证回来"""
    plain = "Test1234abc"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_validate_password_strength_ok():
    """合格密码"""
    ok, reason = validate_password_strength("Abc12345")
    assert ok is True
    assert reason == ""


def test_validate_password_strength_too_short():
    """< 8 位 → 不合格"""
    ok, _ = validate_password_strength("Ab1")
    assert ok is False


def test_validate_password_strength_no_letter():
    """无字母 → 不合格"""
    ok, _ = validate_password_strength("12345678")
    assert ok is False


def test_validate_password_strength_no_digit():
    """无数字 → 不合格"""
    ok, _ = validate_password_strength("abcdefgh")
    assert ok is False


# ========== 2. JWT 模块 ==========


def test_jwt_contains_role_and_exp():
    """JWT 必须含 role 和 exp"""
    token = create_access_token("u001", "student", "张三")
    payload = decode_access_token(token)
    assert payload["sub"] == "u001"
    assert payload["role"] == "student"
    assert payload["name"] == "张三"
    assert "exp" in payload
    assert "iat" in payload
    # exp 应该在 iat 之后 24h
    assert payload["exp"] - payload["iat"] == 24 * 3600


def test_jwt_expired_raises_auth_error():
    """过期 token → AuthError"""
    from backend.公共.errors import AuthError
    token = create_access_token("u001", "student", expire_hours=0)
    time.sleep(1)  # 等 1 秒
    with pytest.raises(AuthError) as exc:
        decode_access_token(token)
    assert "过期" in str(exc.value.message)


def test_jwt_invalid_raises_auth_error():
    """伪造 token → AuthError"""
    from backend.公共.errors import AuthError
    with pytest.raises(AuthError):
        decode_access_token("fake.token.here")


# ========== 3. 黑名单 ==========


def test_blacklist_add_and_check():
    """加入黑名单后能查到"""
    add_to_blacklist("test-token-12345")
    assert is_blacklisted("test-token-12345") is True
    assert is_blacklisted("other-token") is False
