"""重置 A 区所有用户画像 → seed 原始值（仅用于测试隔离）"""
import asyncio
from sqlalchemy import delete, select

from backend.a_用户与聊天.db import get_session
from backend.a_用户与聊天.models.learner_profile import LearnerProfile
from backend.a_用户与聊天.models.user import User
from backend.a_用户与聊天.auth.passwords import hash_password


SEED_PROFILES = {
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


async def main():
    async with get_session() as session:
        # 1. 清空所有画像
        await session.execute(delete(LearnerProfile))

        # 2. 按 seed 重新插入
        for user_id, p in SEED_PROFILES.items():
            user = await session.get(User, user_id)
            if user is None:
                print(f"⚠️  用户 {user_id} 不存在，跳过画像")
                continue
            lp = LearnerProfile(
                user_id=user_id,
                education=p["education"],
                major=p["major"],
                theory_test_score=p["theory_test_score"],
                weak_kps=p["weak_kps"],
                strong_kps=p["strong_kps"],
            )
            session.add(lp)
        print("✅ learner_profile 已重置为 seed 原始值")


if __name__ == "__main__":
    asyncio.run(main())
