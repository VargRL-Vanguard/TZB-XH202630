"""
S-02 单测：auth_middleware 的 get_current_user / require_auth / require_role。

**覆盖**（≥ 6 用例满足 S-02 验收标准）：
1. test_get_current_user_happy_path       正常 token → 返回完整 user dict（含画像）
2. test_get_current_user_missing_header   缺 Authorization 头 → 401
3. test_get_current_user_invalid_token    伪造 token → 401
4. test_get_current_user_expired_token    过期 token → 401
5. test_get_current_user_blacklisted      黑名单 token → 401
6. test_get_current_user_no_profile       老师无画像 → learnerProfile = None
7. test_require_auth_ok                   闸门放行
8. test_require_auth_no_token             闸门拒 401
9. test_require_role_admin_ok             admin 角色通过
10. test_require_role_student_blocked      student 访问 admin 路由 → 403
11. test_require_role_multiple_allowed    teacher/admin 都允许
12. test_require_role_no_roles_arg        工厂必须至少 1 个角色
"""
import time
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from backend.公共.config import settings
from backend.公共.errors import BizError
from backend.公共.response import fail
from backend.公共.auth_middleware import (
    get_current_user,
    require_auth,
    require_role,
)
from backend.a_用户与聊天.auth.tokens import create_access_token
from backend.a_用户与聊天.auth.blacklist import add_to_blacklist, clear_blacklist


# ========== TestApp：用真路由挂载中间件，方便测依赖 ==========

app = FastAPI()


@app.exception_handler(BizError)
async def _biz_error_handler(request: Request, exc: BizError) -> JSONResponse:
    """把 BizError → 标准 {code, message, data} JSON 响应（与 backend.main 行为一致）"""
    return JSONResponse(
        status_code=exc.code,
        content=fail(code=exc.code, message=exc.message, data=exc.data),
    )


@app.get("/whoami")
async def whoami(user: dict = Depends(get_current_user)):
    """返回 user dict（测 get_current_user 完整输出）"""
    return user


@app.get("/protected", dependencies=[Depends(require_auth)])
async def protected():
    return {"ok": True}


@app.get("/admin-only", dependencies=[Depends(require_role("admin"))])
async def admin_only():
    return {"ok": True}


@app.get("/teacher-or-admin", dependencies=[Depends(require_role("teacher", "admin"))])
async def teacher_or_admin():
    return {"ok": True}


client = TestClient(app)


# ========== 工具：构造一个过期 token（不依赖 settings.JWT_EXPIRE_HOURS）==========

def _make_expired_token(user_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub":  user_id,
        "role": role,
        "name": "过期用户",
        "iat":  int((now - timedelta(hours=2)).timestamp()),
        "exp":  int((now - timedelta(hours=1)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _make_tampered_token() -> str:
    """用错误 secret 签发的 token → decode 时签名校验失败"""
    payload = {"sub": "u001", "role": "student", "exp": int(time.time()) + 3600}
    return jwt.encode(payload, "WRONG_SECRET_xxxxxxxxxxxxxxx", algorithm=settings.JWT_ALGORITHM)


# ========== Fixtures ==========

@pytest.fixture(autouse=True)
def _clean_blacklist():
    """每个 case 前清空黑名单，避免上一个 case 干扰"""
    clear_blacklist()
    yield
    clear_blacklist()


# ========== 1. get_current_user ==========

def test_get_current_user_happy_path():
    """正常 token → 返回完整 user dict（含画像）"""
    token = create_access_token("u001", "student", "张三")
    resp = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["userId"] == "u001"
    assert data["name"] == "张三"
    assert data["role"] == "student"
    # student001 在 seed_data.py 有画像
    assert data["learnerProfile"] is not None
    assert "weakKPs" in data["learnerProfile"]
    assert "strongKPs" in data["learnerProfile"]
    assert "theoryTestScore" in data["learnerProfile"]
    assert "education" in data["learnerProfile"]


def test_get_current_user_missing_header():
    """缺 Authorization 头 → 401"""
    resp = client.get("/whoami")
    assert resp.status_code == 401


def test_get_current_user_invalid_token():
    """伪造 token（错签名）→ 401"""
    resp = client.get(
        "/whoami",
        headers={"Authorization": f"Bearer {_make_tampered_token()}"},
    )
    assert resp.status_code == 401


def test_get_current_user_expired_token():
    """过期 token → 401"""
    resp = client.get(
        "/whoami",
        headers={"Authorization": f"Bearer {_make_expired_token('u001', 'student')}"},
    )
    assert resp.status_code == 401


def test_get_current_user_blacklisted():
    """登出后 token → 401"""
    token = create_access_token("u001", "student", "张三")
    add_to_blacklist(token)

    resp = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_get_current_user_no_profile():
    """老师（teacher001）无画像 → learnerProfile = None（不抛错）"""
    token = create_access_token("t001", "teacher", "李老师")
    resp = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["userId"] == "t001"
    assert data["role"] == "teacher"
    assert data["learnerProfile"] is None  # 关键：None 而非抛错


# ========== 2. require_auth 闸门 ==========

def test_require_auth_ok():
    """已登录 → 200"""
    token = create_access_token("u001", "student", "张三")
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_require_auth_no_token():
    """未登录 → 401"""
    resp = client.get("/protected")
    assert resp.status_code == 401


# ========== 3. require_role 工厂 ==========

def test_require_role_admin_ok():
    """admin 角色访问 admin 路由 → 200"""
    token = create_access_token("a001", "admin", "管理员")
    resp = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_require_role_student_blocked():
    """student 角色访问 admin 路由 → 403（注意不是 401）"""
    token = create_access_token("u001", "student", "张三")
    resp = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_require_role_multiple_allowed():
    """teacher / admin 两个都允许时，teacher 也能通过"""
    token = create_access_token("t001", "teacher", "李老师")
    resp = client.get("/teacher-or-admin", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_require_role_no_roles_arg():
    """工厂至少需要一个角色，否则 ValueError"""
    with pytest.raises(ValueError):
        require_role()


# ========== 4. 错误格式（不是 Bearer 开头）==========

def test_get_current_user_wrong_scheme():
    """Authorization 头不是 Bearer 开头 → 401"""
    token = create_access_token("u001", "student", "张三")
    resp = client.get("/whoami", headers={"Authorization": f"Basic {token}"})
    assert resp.status_code == 401
