"""
B 区种子数据：为 A 区已有用户（u001 张三 / u002 李四）补学情画像 + 学习活动。

背景：B 区 Student/Activity 表此前只有测试用例造数，无启动种子，
前端 Dashboard/Activity 真数据联调会 404「学生不存在」。

数值口径：源自 test_profiles/profile_01_本科应届生.json（u001≈高分档）
与 profile_02_高职在读生.json（u002≈低分档），活动日期取当前周（契约禁止过期日期）。

用法：python -m backend.b_学情数据.seed_data
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from backend.b_学情数据.db import create_all_tables, get_session
from backend.b_学情数据.models.student import Student
from backend.b_学情数据.models.activity import Activity

# u001 张三：本科应届生画像（p-001 口径）
U001 = dict(
    student_id="u001", name="张三",
    study_hours=86.5, completion_rate=0.82, avg_score=82.4, trend="up", trend_value=0.32,
    dims=dict(comprehension=88, application=82, analysis=85, evaluation=78, creation=74, collaboration=80),
    kps=dict(kp01=92, kp02=88, kp03=85, kp04=80, kp05=66, kp06=58),
)

# u002 李四：高职在读生画像（p-002 口径，低分档触发降维演示）
U002 = dict(
    student_id="u002", name="李四",
    study_hours=41.0, completion_rate=0.48, avg_score=58.6, trend="down", trend_value=-0.21,
    dims=dict(comprehension=62, application=48, analysis=42, evaluation=38, creation=35, collaboration=55),
    kps=dict(kp01=65, kp02=52, kp03=44, kp04=38, kp05=30, kp06=25),
)

KP_NAMES = {
    "kp01": "工业机器人基础", "kp02": "工业机器人坐标系", "kp03": "PLC 编程基础",
    "kp04": "传感器与检测技术", "kp05": "工业互联网通信", "kp06": "智能制造系统集成",
}

# (类型, 资源名, 状态, 进度, 得分, kp, 天偏移, 分钟)
U001_ACTS = [
    ("test", "工业机器人基础理论测验", "completed", 100, 92, ["kp01"], 0, 40),
    ("course", "工业机器人路径规划", "completed", 100, 90, ["kp02"], 1, 55),
    ("exercise", "PLC梯形图编程练习", "completed", 100, 88, ["kp03"], 2, 50),
    ("course", "D-H参数法建模精讲", "completed", 100, 78, ["kp02"], 3, 60),
    ("test", "顺控程序SFC概念测验", "completed", 100, 68, ["kp03"], 4, 30),
    ("exercise", "传感器选型综合实训", "in-progress", 60, None, ["kp04"], 5, 45),
    ("course", "工业互联网通信入门", "in-progress", 35, None, ["kp05"], 6, 25),
]

U002_ACTS = [
    ("course", "工业机器人基础（入门篇）", "completed", 100, 72, ["kp01"], 0, 35),
    ("exercise", "坐标系基础练习", "completed", 100, 55, ["kp02"], 1, 30),
    ("course", "PLC 编程基础（图解版）", "in-progress", 50, None, ["kp03"], 3, 40),
    ("test", "传感器概念小测", "completed", 100, 48, ["kp04"], 5, 25),
    ("discussion", "转岗学习经验交流", "completed", 100, None, ["kp06"], 6, 20),
]


async def seed() -> None:
    await create_all_tables()
    now = datetime.now()
    async with get_session() as session:
        for prof, acts in ((U001, U001_ACTS), (U002, U002_ACTS)):
            if await session.get(Student, prof["student_id"]) is None:
                session.add(Student(
                    student_id=prof["student_id"], name=prof["name"],
                    study_hours=prof["study_hours"], completion_rate=prof["completion_rate"],
                    avg_score=prof["avg_score"], trend=prof["trend"], trend_value=prof["trend_value"],
                    dim_comprehension=prof["dims"]["comprehension"],
                    dim_application=prof["dims"]["application"],
                    dim_analysis=prof["dims"]["analysis"],
                    dim_evaluation=prof["dims"]["evaluation"],
                    dim_creation=prof["dims"]["creation"],
                    dim_collaboration=prof["dims"]["collaboration"],
                ))
                print(f"✅ Student {prof['student_id']} {prof['name']}")
            # 活动（幂等：按 student 清空重种，保证日期始终是当前周）
            from sqlalchemy import delete
            await session.execute(delete(Activity).where(Activity.student_id == prof["student_id"]))
            for (typ, rname, status, prog, score, kps, day_ago, minutes) in acts:
                start = now - timedelta(days=day_ago, hours=2)
                session.add(Activity(
                    activity_id=f"act-{uuid.uuid4().hex[:12]}",
                    student_id=prof["student_id"],
                    activity_type=typ, resource_id="", resource_name=rname, resource_type=typ,
                    status=status, progress=prog, score=score,
                    start_time=start, end_time=start + timedelta(minutes=minutes),
                    duration_minutes=minutes, kp_tags=kps,
                ))
            print(f"✅ Activity {prof['student_id']} × {len(acts)}（当前周）")


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed())
