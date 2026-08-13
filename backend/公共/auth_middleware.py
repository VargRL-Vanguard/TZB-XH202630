"""
S-02 统一鉴权中间件。

**给 B/C/D 用**（替代各自手写 token 解析）：

    from backend.公共.auth_middleware import get_current_user, require_auth, require_role

    # 1. 注入当前用户（返回 dict）
    @router.get("/api/some_resource")
    async def get_resource(user: dict = Depends(get_current_user)):
        user_id = user["userId"]
        role    = user["role"]
        # learnerProfile: {education, theoryTestScore, weakKPs[], strongKPs[]} 或 None

    # 2. 路由级鉴权（无入参路由）
    @router.get("/api/protected", dependencies=[Depends(require_auth)])
    async def protected():
        ...

    # 3. 角色装饰器
    @router.post("/api/admin/x", dependencies=[Depends(require_role("admin"))])
    async def admin_only():
        ...

**返回结构契约**（与 api-doc.js §1.3 + 任务 2 契约对齐）：
    {
      "userId": "u001",
      "name":   "张三",
      "role":   "student",
      "learnerProfile": {                   # 学生可能有，老师/管理员可能为 None
          "education":       "本科",
          "theoryTestScore": 78,
          "weakKPs":         ["kp12", "kp15"],
          "strongKPs":       ["kp03"]
      } | None
    }

**为什么不直接复用 a_用户与聊天/user/deps.py**：
- 那个文件返回的是 JWT 原始 payload（sub/role/name/exp），**不含** learnerProfile
- B/C/D 拿到 user 必须能直接读 weakKPs/strongKPs，**不能**再调 A 的 get_learner_profile
- 所以这里在 get_current_user 里**主动**查 A 的 learner_profile 表并合进去
- 老师/管理员没画像 → learnerProfile = None（前端按 None 走"无画像"分支）

**实现要点**：
- get_current_user 是 async 依赖（需要查 DB 拿画像）
- @require_auth / @require_role 是不返回值的"闸门"装饰器，返回 None
- 失败一律抛 AuthError (401) 或 ForbiddenError (403)，由全局异常处理器转 JSON
"""
from typing import Any, Callable, Optional

from fastapi import Depends, Header

from backend.公共.errors import AuthError, ForbiddenError
from backend.a_用户与聊天.auth.tokens import decode_access_token
from backend.a_用户与聊天.auth.blacklist import is_blacklisted


# ---------- 内部工具 ----------

def _extract_bearer_token(authorization: Optional[str]) -> str:
    """从 Authorization: Bearer <token> 提取 token。"""
    if not authorization:
        raise AuthError("缺少 Authorization 头")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthError("Authorization 头格式错误（应为 'Bearer <token>'）")
    return parts[1].strip()


async def _load_learner_profile(user_id: str) -> Optional[dict]:
    """
    从 A 区 learner_profile 表读画像并转成契约结构。
    - 查不到（学生没建 / 老师 / 管理员）→ 返回 None
    - DB 异常 → 让异常往上抛（不让鉴权静默成功）
    """
    # 局部 import 避免公共模块加载时触发 A 区 DB 引擎初始化
    from backend.a_用户与聊天.db import get_learner_profile

    raw = await get_learner_profile(user_id)
    if raw is None:
        return None
    return {
        "education":       raw.get("education", ""),
        "theoryTestScore": raw.get("theory_test_score"),
        "weakKPs":         raw.get("weak_kps") or [],
        "strongKPs":       raw.get("strong_kps") or [],
    }


# ---------- 核心依赖：get_current_user ----------

async def get_current_user(
    authorization: str | None = Header(default=None),
) -> dict:
    """
    FastAPI 依赖：解析 Authorization 头 + 验签 + 查黑名单 + 合并画像。

    :return: dict {userId, name, role, learnerProfile}
    :raises AuthError: 401（缺头 / 格式错 / token 无效 / 过期 / 已登出）
    """
    token = _extract_bearer_token(authorization)

    # 1. 解码 + 验证签名 + 验证 exp
    payload = decode_access_token(token)

    # 2. 检查黑名单
    if is_blacklisted(token):
        raise AuthError("token 已失效（已登出）")

    user_id = payload["sub"]
    role    = payload["role"]
    name    = payload.get("name", "")

    # 3. 合并学习者画像（学生可能有；老师/管理员为 None）
    learner_profile = await _load_learner_profile(user_id)

    return {
        "userId":         user_id,
        "name":           name,
        "role":           role,
        "learnerProfile": learner_profile,
    }


# ---------- 闸门依赖：require_auth ----------

async def require_auth(
    user: dict = Depends(get_current_user),
) -> None:
    """
    路由级"必须登录"装饰器。返回 None，配合 dependencies=[Depends(require_auth)] 用。

    这里只做"已登录"校验，user 不暴露给下游（用 get_current_user 才能拿到 user）。
    """
    if not user or "userId" not in user:
        raise AuthError("未登录")


# ---------- 闸门依赖：require_role ----------

def require_role(*allowed_roles: str) -> Callable[..., Any]:
    """
    路由级"必须指定角色"装饰器工厂。

    用法：
        dependencies=[Depends(require_role("admin"))]
        dependencies=[Depends(require_role("teacher", "admin"))]

    :param allowed_roles: 允许的角色列表（student/teacher/admin）
    """
    if not allowed_roles:
        raise ValueError("require_role 至少需要一个角色")

    allowed = set(allowed_roles)

    async def _checker(user: dict = Depends(get_current_user)) -> None:
        if not user or "role" not in user:
            raise AuthError("未登录")
        if user["role"] not in allowed:
            # 鉴权成功（已登录）但角色不符 → 403 而非 401
            raise ForbiddenError(
                f"需要角色 {sorted(allowed)}，当前角色 {user['role']}"
            )

    return _checker
