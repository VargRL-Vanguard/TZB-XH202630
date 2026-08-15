"""
A-02 用户信息 + 学习者画像单测。

**覆盖场景**（A-02 验收标准）：
1. 自己读自己 → 200
2. 跨学生读他人 → 403
3. 教师读学生 → 200
4. 管理员读任何人 → 200
5. 鉴权缺失 / token 错 → 401
6. 用户不存在 → 404
7. PUT /profile 越权（student 改他人）→ 403
8. PUT /profile teacher 改学生 → 200
9. PUT /profile 不存在的 userId（admin）→ 404

**前提**：先跑 `python -m backend.a_用户与聊天.seed_data`，里面已有：
- u001 student001（student，有画像）
- u002 student002（student，有画像）
- u003 teacher001（teacher，无画像）
- u004 admin001（admin，无画像）—— 这里如果没有就补
"""
import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.a_用户与聊天.auth.tokens import create_access_token
from backend.a_用户与聊天.db import get_session, upsert_learner_profile

# 与 seed_data.py 保持一致的种子画像（测试改完必须恢复，避免污染其他测试）
_SEED_PROFILES = {
    "u001": {
        "education": "本科",
        "major": "机械工程",
        "theory_test_score": 78,
        "weak_kps": ["kp12", "kp15"],
        "strong_kps": ["kp03", "kp07"],
    },
    "u002": {
        "education": "本科",
        "major": "软件工程",
        "theory_test_score": 85,
        "weak_kps": ["kp08"],
        "strong_kps": ["kp01", "kp02", "kp03"],
    },
}


async def _restore_profile(user_id: str) -> None:
    """把被测用户画像恢复为 seed_data.py 的初始值。"""
    seed = _SEED_PROFILES.get(user_id)
    if seed:
        await upsert_learner_profile(user_id, **seed)


# ========== 辅助：生成指定用户 token ==========

def _token(user_id: str, role: str) -> str:
    return create_access_token(user_id=user_id, role=role, name=user_id)


# ========== 1. GET /api/user/info 鉴权 + 越权矩阵 ==========

@pytest.mark.asyncio
async def test_info_self_ok():
    """case 1: 学生读自己 → 200"""
    token = _token("u001", "student")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(
            "/api/user/info?userId=u001",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["userId"] == "u001"
    assert data["role"] == "student"
    assert "weakKPs" in data
    assert "strongKPs" in data


@pytest.mark.asyncio
async def test_info_cross_student_forbidden():
    """case 2: 学生 u001 读 u002 → 403"""
    token = _token("u001", "student")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(
            "/api/user/info?userId=u002",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_info_teacher_read_student_ok():
    """case 3: 教师读学生 → 200"""
    token = _token("t001", "teacher")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(
            "/api/user/info?userId=u001",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["userId"] == "u001"


@pytest.mark.asyncio
async def test_info_admin_read_any_ok():
    """case 4: 管理员读任何学生 → 200"""
    token = _token("u004", "admin")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(
            "/api/user/info?userId=u002",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_info_missing_auth():
    """case 5: 没带 token → 401"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/user/info?userId=u001")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_info_invalid_token():
    """case 5b: token 错 → 401"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(
            "/api/user/info?userId=u001",
            headers={"Authorization": "Bearer not-a-real-jwt-token"},
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_info_user_not_found():
    """case 6: 用户不存在 → 404"""
    token = _token("u004", "admin")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(
            "/api/user/info?userId=u999",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 404


# ========== 2. PUT /api/user/profile 越权 + 业务 ==========

@pytest.mark.asyncio
async def test_profile_student_self_update_ok():
    """case 7: 学生改自己 → 200，画像更新"""
    token = _token("u001", "student")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.put(
            "/api/user/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "education": "本科",
                "major": "计算机科学",
                "theoryTestScore": 88,
                "weakKPs": ["kp001", "kp002"],
                "strongKPs": ["kp100"],
            },
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["userId"] == "u001"
    assert data["education"] == "本科"
    assert data["theoryTestScore"] == 88
    assert "kp001" in data["weakKPs"]

    # 恢复种子数据（本测试连真实 MySQL，改完必须还原）
    await _restore_profile("u001")


@pytest.mark.asyncio
async def test_profile_student_update_other_forbidden():
    """case 8: 学生 u001 想改 u002（带 userId 参数）→ 403"""
    token = _token("u001", "student")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.put(
            "/api/user/profile?userId=u002",
            headers={"Authorization": f"Bearer {token}"},
            json={"education": "本科"},
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_profile_teacher_update_student_ok():
    """case 9: 教师改学生（带 userId） → 200"""
    token = _token("t001", "teacher")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.put(
            "/api/user/profile?userId=u002",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "education": "硕士",
                "major": "人工智能",
                "theoryTestScore": 92,
                "weakKPs": ["kp050"],
                "strongKPs": [],
            },
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["userId"] == "u002"
    assert data["education"] == "硕士"
    assert data["theoryTestScore"] == 92

    # 恢复种子数据（本测试连真实 MySQL，改完必须还原）
    await _restore_profile("u002")


@pytest.mark.asyncio
async def test_profile_admin_update_nonexistent_user():
    """case 10: admin 改不存在的用户 → 404"""
    token = _token("u004", "admin")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.put(
            "/api/user/profile?userId=u999",
            headers={"Authorization": f"Bearer {token}"},
            json={"education": "本科"},
        )
    assert resp.status_code == 404


# ========== 3. 业务流：upsert 行为 ==========

@pytest.mark.asyncio
async def test_profile_partial_update_preserves_other_fields():
    """case 11: 只更新部分字段，其他字段不动"""
    # 先确保 u002 有画像
    await upsert_learner_profile(
        "u002",
        education="本科",
        major="机械工程",
        theory_test_score=75,
        weak_kps=["kp010"],
        strong_kps=["kp200"],
    )

    token = _token("u002", "student")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 只改 education，其他保留
        resp = await ac.put(
            "/api/user/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={"education": "硕士"},
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["education"] == "硕士"  # 改了
    assert data["major"] == "机械工程"   # 没动
    assert data["theoryTestScore"] == 75  # 没动
    assert data["weakKPs"] == ["kp010"]   # 没动

    # 恢复种子数据（本测试连真实 MySQL，改完必须还原）
    await _restore_profile("u002")


@pytest.mark.asyncio
async def test_profile_theory_score_out_of_range():
    """case 12: theoryTestScore 越界（>100）→ 422（FastAPI 校验）"""
    token = _token("u001", "student")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.put(
            "/api/user/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={"theoryTestScore": 150},
        )
    assert resp.status_code == 422
