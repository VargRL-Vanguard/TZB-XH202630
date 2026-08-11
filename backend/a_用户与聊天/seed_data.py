"""
A-00 种子数据：3 个测试用户 + 2 个学习者画像。
密码用 SHA256 临时占位（A-01 任务会换成 bcrypt）。

用法：
    cd D:\\TZB\\TZB-XH202630
    python -m backend.a_用户与聊天.seed_data
"""
import asyncio
import hashlib

from sqlalchemy import select

from backend.a_用户与聊天.db import get_session
from backend.a_用户与聊天.models.user import User
from backend.a_用户与聊天.models.learner_profile import LearnerProfile


def _fake_hash(pwd: str) -> str:
    """临时 SHA256 占位（**生产前必须换成 bcrypt**，A-01 任务实现）。"""
    return hashlib.sha256(pwd.encode()).hexdigest()


# 测试账号：用户名 / 密码统一 Test@1234
SEED_USERS = [
    {
        "id": "u001",
        "username": "student001",
        "password_hash": _fake_hash("Test@1234"),
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
        "password_hash": _fake_hash("Test@1234"),
        "name": "李四",
        "role": "student",
        "profile": {
            "education": "硕士",
            "major": "计算机科学",
            "theory_test_score": 85,
            "weak_kps": ["kp22"],
            "strong_kps": ["kp01", "kp02", "kp05"],
        },
    },
    {
        "id": "t001",
        "username": "teacher001",
        "password_hash": _fake_hash("Test@1234"),
        "name": "王老师",
        "role": "teacher",
        "profile": None,  # 教师无画像
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
                password_hash=u["password_hash"],
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
