"""
A-03 聊天消息 4 接口单测。

**覆盖**（满足任务清单 A-03 验收标准）：
- send:      happy / 越权 userId / 给自己发 / target 不存在 / type 枚举
- history:   happy / 分页 / 越权 / 双向（我→他 + 他→我）
- list:      happy / 未读计数
- read:      happy / 标后再查 status 变 read / 越权 userId
- 鉴权:      缺 token → 401

**前提**：先跑 init_db.py 建表 + seed_data.py 灌用户。
"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, delete

from backend.main import app
from backend.a_用户与聊天.auth.tokens import create_access_token
from backend.a_用户与聊天.db import get_session
from backend.a_用户与聊天.models.message import Message


# ========== 辅助 ==========

def _token(user_id: str, role: str = "student", name: str = "") -> str:
    return create_access_token(user_id=user_id, role=role, name=name or user_id)


async def _clean_messages():
    """每个 case 前清空 message 表，避免顺序干扰"""
    async with get_session() as session:
        await session.execute(delete(Message))


@pytest.fixture(autouse=True)
async def _reset_messages():
    await _clean_messages()
    yield
    await _clean_messages()


# ========== 1. POST /api/chat/send ==========

@pytest.mark.asyncio
async def test_send_happy_path():
    """正常发送：u001 → u002"""
    token = _token("u001")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/chat/send",
            headers={"Authorization": f"Bearer {token}"},
            json={"userId": "u001", "targetId": "u002", "content": "你好", "type": "text"},
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "sent"
    assert data["id"] > 0
    assert "timestamp" in data

    # 校验确实写库了
    async with get_session() as session:
        rows_q = await session.execute(select(Message))
        rows = rows_q.scalars().all()
    assert len(rows) == 1
    assert rows[0].content == "你好"
    assert rows[0].status == "sent"


@pytest.mark.asyncio
async def test_send_type_image():
    """image 类型"""
    token = _token("u001")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/chat/send",
            headers={"Authorization": f"Bearer {token}"},
            json={"userId": "u001", "targetId": "u002", "content": "/img/1.png", "type": "image"},
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_send_type_file():
    """file 类型"""
    token = _token("u001")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/chat/send",
            headers={"Authorization": f"Bearer {token}"},
            json={"userId": "u001", "targetId": "u002", "content": "/file/a.pdf", "type": "file"},
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_send_wrong_userid_forbidden():
    """userId 写别人 → 400（不允许冒用身份）"""
    token = _token("u001")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/chat/send",
            headers={"Authorization": f"Bearer {token}"},
            json={"userId": "u002", "targetId": "u002", "content": "hi"},  # 给自己
        )
    # 冒用 u002 + 给自己发 → 400
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_send_to_self_forbidden():
    """不能给自己发"""
    token = _token("u001")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/chat/send",
            headers={"Authorization": f"Bearer {token}"},
            json={"userId": "u001", "targetId": "u001", "content": "hi"},
        )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_send_target_not_found():
    """targetId 不存在 → 404"""
    token = _token("u001")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/chat/send",
            headers={"Authorization": f"Bearer {token}"},
            json={"userId": "u001", "targetId": "ghost999", "content": "hi"},
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_send_missing_token_401():
    """无 token → 401"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/chat/send",
            json={"userId": "u001", "targetId": "u002", "content": "hi"},
        )
    assert resp.status_code == 401


# ========== 2. GET /api/chat/history ==========

async def _seed_chat_data():
    """灌 5 条消息：u001→u002 三条（已读/未读混合），u002→u001 两条"""
    async with get_session() as session:
        for i, (sender, target, status) in enumerate([
            ("u001", "u002", "read"),
            ("u001", "u002", "sent"),
            ("u001", "u002", "sent"),
            ("u002", "u001", "read"),
            ("u002", "u001", "sent"),
        ]):
            session.add(Message(
                user_id=sender, target_id=target, content=f"msg{i}",
                type="text", status=status,
            ))


@pytest.mark.asyncio
async def test_history_bidirectional():
    """双向消息都能拉到"""
    await _seed_chat_data()
    token = _token("u001")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(
            "/api/chat/history?userId=u001&targetId=u002",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total"] == 5
    assert len(data["list"]) == 5
    # 升序
    for i in range(len(data["list"]) - 1):
        assert data["list"][i]["timestamp"] <= data["list"][i + 1]["timestamp"]


@pytest.mark.asyncio
async def test_history_pagination():
    """分页：limit=2 offset=0 → 前 2 条；offset=2 → 第 3、4 条"""
    await _seed_chat_data()
    token = _token("u001")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r1 = await ac.get(
            "/api/chat/history?userId=u001&targetId=u002&limit=2&offset=0",
            headers={"Authorization": f"Bearer {token}"},
        )
        r2 = await ac.get(
            "/api/chat/history?userId=u001&targetId=u002&limit=2&offset=2",
            headers={"Authorization": f"Bearer {token}"},
        )
        r3 = await ac.get(
            "/api/chat/history?userId=u001&targetId=u002&limit=2&offset=4",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert r1.json()["data"]["total"] == 5
    assert len(r1.json()["data"]["list"]) == 2
    assert r1.json()["data"]["hasMore"] is True

    assert len(r2.json()["data"]["list"]) == 2
    assert r2.json()["data"]["hasMore"] is True

    assert len(r3.json()["data"]["list"]) == 1
    assert r3.json()["data"]["hasMore"] is False


@pytest.mark.asyncio
async def test_history_wrong_userid_forbidden():
    """学生查他人历史 → 400"""
    await _seed_chat_data()
    token = _token("u001")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(
            "/api/chat/history?userId=u002&targetId=u001",  # u001 查 u002 的历史
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_history_teacher_can_query_any():
    """教师可查任意两人（userId 任意）"""
    await _seed_chat_data()
    token = _token("t001", "teacher", "王老师")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(
            "/api/chat/history?userId=u001&targetId=u002",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200


# ========== 3. GET /api/chat/list ==========

@pytest.mark.asyncio
async def test_list_with_unread_count():
    """会话列表：未读数 = 1（u002→u001 的 sent 那条）"""
    await _seed_chat_data()
    token = _token("u001")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(
            "/api/chat/list?userId=u001",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert len(items) == 1
    assert items[0]["targetId"] == "u002"
    assert items[0]["name"] == "李四"
    assert items[0]["unread"] == 1  # u002→u001 的 "sent" 那条


@pytest.mark.asyncio
async def test_list_empty():
    """无任何消息时返回空数组"""
    token = _token("u001")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(
            "/api/chat/list?userId=u001",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    assert resp.json()["data"] == []


# ========== 4. POST /api/chat/read ==========

@pytest.mark.asyncio
async def test_read_marks_sent_to_read():
    """标已读：所有 target→self 且 status=sent 的都改成 read"""
    await _seed_chat_data()
    token = _token("u001")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/chat/read",
            headers={"Authorization": f"Bearer {token}"},
            json={"userId": "u001", "targetId": "u002"},
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["success"] is True
    assert data["markedCount"] == 1  # u002→u001 有一条 "sent"

    # 校验：所有 u002→u001 都是 read 了
    async with get_session() as session:
        rows_q = await session.execute(
            select(Message).where(
                (Message.user_id == "u002") & (Message.target_id == "u001")
            )
        )
        rows = rows_q.scalars().all()
    assert all(r.status == "read" for r in rows)


@pytest.mark.asyncio
async def test_read_wrong_userid_forbidden():
    """userId 写别人 → 400"""
    token = _token("u001")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/chat/read",
            headers={"Authorization": f"Bearer {token}"},
            json={"userId": "u002", "targetId": "u001"},  # u001 不能标 u002 的已读
        )
    assert resp.status_code == 400
