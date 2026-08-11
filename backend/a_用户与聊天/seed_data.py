"""
A-00 种子数据：3 个测试用户 + 2 个学习者画像。
**密码**：统一 Test@1234（A-01 实现了 bcrypt，所以这里也用 bcrypt 哈希）

**用法**：
    cd D:\\TZB\\TZB-XH202630
    python -m backend.a_用户与聊天.seed_data
"""
import asyncio

from sqlalchemy import select

from backend.a_用户与聊天.db import get_session
from backend.a_用户与聊天.auth.passwords import hash_password
from backend.a_用户与聊天.models.user import User
from backend.a_用户与聊天.models.learner_profile import LearnerProfile


# 测试账号：用户名 / 密码统一 Test@1234（明文，在 main() 里 bcrypt 哈希）
SEED_USERS = [
    {
        "id": "u001",
        "username": "student001",
        "password": "Test@1234",
        "name": "张三",
        "role": "student",
        "profile": {
            "education": "本科",
            "major": "机械工程",
            "theory_test_score": 78,
            "weak_kps": ["kp12", "kp15"],
            "strong_kps": ["kp03", "kp07"],
        },
    },
    {
        "id": "u002",
        "username": "student002",
        "password": "Test@1234",
        "name": "李四",
        "role": "student",
        "profile": {
            "education": "本科",
            "major": "软件工程",
            "theory_test_score": 85,
            "weak_kps": ["kp08"],
            "strong_kps": ["kp01", "kp02", "kp03"],
        },
    },
    {
        "id": "t001",
        "username": "teacher001",
        "password": "Test@1234",
        "name": "王老师",
        "role": "teacher",
        "profile": None,
    },
]


async def main() -> None:
    print("=" * 60)
    print("  A-00 种子数据写入")
    print("=" * 60)

    async with get_session() as session:
        for u in SEED_USERS:
            # 检查是否已存在
            existing = await session.get(User, u["id"])
            if existing:
                print(f"⏭️  跳过已存在：{u['username']}")
                continue

            user = User(
                id=u["id"],
                username=u["username"],
                password_hash=hash_password(u["password"]),  # A-01 bcrypt 哈希
                name=u["name"],
                role=u["role"],
            )
            session.add(user)
            # 关键：先 flush 让 user 立刻 INSERT 到 DB（避免外键失败）
            await session.flush()

            if u["profile"]:
                p = u["profile"]
                profile = LearnerProfile(
                    user_id=u["id"],
                    education=p["education"],
                    major=p["major"],
                    theory_test_score=p["theory_test_score"],
                    weak_kps=p["weak_kps"],
                    strong_kps=p["strong_kps"],
                )
                session.add(profile)
                # 关键：profile 也 flush 一下
                await session.flush()
                print(f"✅ 创建用户 {u['username']} + 画像（weak={p['weak_kps']}）")
            else:
                print(f"✅ 创建用户 {u['username']}（无画像）")

    print("-" * 60)
    print("测试账号：")
    print("  student001 / Test@1234  (有画像)")
    print("  student002 / Test@1234  (有画像)")
    print("  teacher001 / Test@1234  (教师，无画像)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
