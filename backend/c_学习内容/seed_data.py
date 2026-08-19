"""
C 区种子数据：为 A 区已有用户（u001 张三 / u002 李四）生成学习路径 + 学习建议。

前置：
    1. 先跑 A 区 seed（保证 u001/u002 用户存在，本脚本不依赖但联调需要）
    2. `python -m backend.main` 启动时已幂等建表（learning_content.db）

口径：与 B 区 test_profiles 对齐
    - u001 本科应届生（profile_01，弱项 kp12d D-H参数法 / kp22c 顺控SFC）→ 认证备考进阶路径
    - u002 高职在读生（profile_02，基础薄弱）→ 基础巩固路径

用法：
    cd D:\\TZB\\TZB-XH202630
    py -m backend.c_学习内容.seed_data
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from backend.c_学习内容.db import get_session
from backend.c_学习内容.models import LearningModule, LearningPath, LearningTask, Suggestion

TODAY = date.today()


def _d(offset_days: int) -> str:
    """相对今天的日期字符串（保证演示数据永不过期）。"""
    return (TODAY + timedelta(days=offset_days)).isoformat()


def _ts(offset_days: int, hour: int = 9, minute: int = 0) -> datetime:
    base = datetime(TODAY.year, TODAY.month, TODAY.day, hour, minute) + timedelta(days=offset_days)
    return base.replace(tzinfo=timezone.utc)


# ============================================================
# u001 张三：本科应届生 · 智能制造工程师认证备考（进阶向）
# ============================================================

U001_MODULES = [
    {
        "name": "机器人基础与坐标系",
        "desc": "工业机器人结构、示教器操作与基座/工具/世界坐标系变换，齐次矩阵推导。",
        "progress": 100, "order_index": 0, "status": "completed",
        "start": _d(-18), "end": _d(-12), "duration": "7天",
        "tasks": [
            {"title": "坐标系变换单元测试", "meta": "测验 · kp12/kp02", "priority": "high", "completed": 1, "due": _d(-13)},
            {"title": "齐次变换矩阵推导复盘", "meta": "复习 · kp12", "priority": "medium", "completed": 1, "due": _d(-12)},
        ],
    },
    {
        "name": "D-H 参数法与运动学建模",
        "desc": "标准/改进 D-H 参数法建模，正逆运动学求解，针对弱项 kp12d 定制强化。",
        "progress": 62, "order_index": 1, "status": "current",
        "start": _d(-11), "end": _d(-1), "duration": "10天",
        "tasks": [
            {"title": "D-H 参数法建模例题精练", "meta": "练习 · kp12d", "priority": "high", "completed": 0, "due": _d(0)},
            {"title": "正运动学推导视频课", "meta": "课程 · kp12d", "priority": "medium", "completed": 1, "due": _d(-2)},
            {"title": "逆运动学数值解法预习", "meta": "预习 · kp12e", "priority": "low", "completed": 0, "due": _d(1)},
        ],
    },
    {
        "name": "顺控程序设计（SFC）",
        "desc": "顺序功能图（SFC）结构与 PLC 顺控实现，修复弱项 kp22c（上次测验 68 分）。",
        "progress": 0, "order_index": 2, "status": "pending",
        "start": _d(0), "end": _d(7), "duration": "8天",
        "tasks": [
            {"title": "SFC 概念测验错题重做", "meta": "测验 · kp22c", "priority": "high", "completed": 0, "due": _d(1)},
            {"title": "单序列 SFC 编程练习", "meta": "练习 · kp22c", "priority": "medium", "completed": 0, "due": _d(4)},
        ],
    },
    {
        "name": "离线编程与路径规划实战",
        "desc": "RoboDK 离线编程、路径优化与碰撞检测，衔接认证实操考点 kp15/kp18。",
        "progress": 0, "order_index": 3, "status": "pending",
        "start": _d(8), "end": _d(19), "duration": "12天",
        "tasks": [
            {"title": "离线编程综合实训", "meta": "实训 · kp15", "priority": "high", "completed": 0, "due": _d(12)},
            {"title": "路径优化案例讨论", "meta": "讨论 · kp18", "priority": "low", "completed": 0, "due": _d(17)},
        ],
    },
    {
        "name": "认证模拟冲刺",
        "desc": "智能制造工程师认证模拟卷 ×2 + 高频考点串讲。",
        "progress": 0, "order_index": 4, "status": "pending",
        "start": _d(20), "end": _d(24), "duration": "5天",
        "tasks": [
            {"title": "认证模拟卷（一）", "meta": "模拟 · 综合", "priority": "high", "completed": 0, "due": _d(21)},
        ],
    },
]

U001_SUGGESTIONS = [
    {"title": "用「先建系再列表」口诀攻克 D-H 参数法", "content": "近 3 次 D-H 建模练习正确率 55%（低于阈值 60%）。建议每次建模先画坐标系简图、再按连杆参数表逐行填 z/x 轴规则，配合《D-H参数法建模精讲》第 3-4 节重看，48 小时内完成 5 道降维例题。", "category": "method", "priority": "high", "is_read": 0, "days": -1},
    {"title": "顺控 SFC 概念补强：从错题出发", "content": "上次《顺控程序SFC概念测验》得 68 分，主要失分在「选择序列分支条件」。建议先重做错题，再看《PLC 梯形图与 SFC 对照》12 分钟微课，最后用单序列→选择序列→并行序列三步递进练习巩固。", "category": "review", "priority": "high", "is_read": 0, "days": -2},
    {"title": "推荐资源：齐次矩阵可视化工具", "content": "配合当前模块《D-H 参数法与运动学建模》，推荐使用坐标系 3D 可视化小工具辅助理解齐次变换的几何意义，每天 10 分钟，连续 5 天。", "category": "resource", "priority": "medium", "is_read": 0, "days": -3},
    {"title": "保持学习节奏：固定每日 19:00-20:00", "content": "近两周学习行为数据显示你的有效学习时段集中在晚间，建议固定 19:00-20:00 为机器人学习时段，配合番茄钟 25+5 循环，预计 4 周后 D-H 模块可达标。", "category": "method", "priority": "medium", "is_read": 1, "days": -5},
    {"title": "练习推荐：逆运动学数值解三题", "content": "你已掌握正运动学推导，推荐进阶练习「逆运动学数值解法」3 题（难度 L4），完成后系统将根据正确率决定是否触发进阶挑战。", "category": "practice", "priority": "medium", "is_read": 0, "days": -6},
    {"title": "坐标系模块已达标，进入巩固期", "content": "《机器人基础与坐标系》模块综合掌握度 92%。建议 7 天后做 1 次间隔复习（15 分钟速测）防遗忘，无需重复刷课。", "category": "review", "priority": "low", "is_read": 1, "days": -8},
    {"title": "资源推荐：认证考点速查手册", "content": "距离智能制造工程师认证约 6 周，推荐「认证高频考点速查手册」，重点覆盖 kp12/kp15/kp22 三大板块，配合冲刺模块使用。", "category": "resource", "priority": "low", "is_read": 1, "days": -9},
    {"title": "讨论区参与度可以再提升", "content": "近 30 天讨论区发言 2 次（同龄平均 6 次）。建议参与本周「离线编程与路径优化」话题讨论，输出 1 条实践观点即可加 5 分过程性评价。", "category": "practice", "priority": "low", "is_read": 1, "days": -12},
]

# ============================================================
# u002 李四：高职在读 · 基础巩固（低分档）
# ============================================================

U002_MODULES = [
    {
        "name": "工业机器人安全操作规范",
        "desc": "安全操作规程、示教器基本操作与急停流程（上岗必修）。",
        "progress": 100, "order_index": 0, "status": "completed",
        "start": _d(-14), "end": _d(-10), "duration": "5天",
        "tasks": [
            {"title": "安全规范测验", "meta": "测验 · kp01", "priority": "high", "completed": 1, "due": _d(-11)},
        ],
    },
    {
        "name": "PLC 梯形图入门",
        "desc": "梯形图基本元件与启保停电路，从零搭建，配降维例题（L2）。",
        "progress": 45, "order_index": 1, "status": "current",
        "start": _d(-9), "end": _d(1), "duration": "10天",
        "tasks": [
            {"title": "启保停电路搭建练习", "meta": "练习 · kp22a", "priority": "high", "completed": 0, "due": _d(0)},
            {"title": "梯形图元件识别卡", "meta": "记忆 · kp22", "priority": "medium", "completed": 0, "due": _d(2)},
        ],
    },
    {
        "name": "传感器基础与选型",
        "desc": "常用传感器原理与选型参数入门，衔接实训岗位需求。",
        "progress": 0, "order_index": 2, "status": "pending",
        "start": _d(2), "end": _d(11), "duration": "10天",
        "tasks": [
            {"title": "传感器选型小测", "meta": "测验 · kp04", "priority": "medium", "completed": 0, "due": _d(8)},
        ],
    },
    {
        "name": "综合实训：单站装卸单元",
        "desc": "综合运用 PLC + 传感器完成单站装卸单元联调。",
        "progress": 0, "order_index": 3, "status": "pending",
        "start": _d(12), "end": _d(25), "duration": "14天",
        "tasks": [
            {"title": "装卸单元联调记录", "meta": "实训 · 综合", "priority": "high", "completed": 0, "due": _d(20)},
        ],
    },
]

U002_SUGGESTIONS = [
    {"title": "从「降维例题」重新起步", "content": "入门测验显示梯形图基础正确率 48%，已为你自动生成 L1 降维版《梯形图第一课》。建议先用 20 分钟完成降维例题，正确率稳定在 80% 后再回到 L2 标准练习。", "category": "resource", "priority": "high", "is_read": 0, "days": -1},
    {"title": "方法建议：先记元件符号再学电路", "content": "建议把常开/常闭/线圈/定时器 4 类元件做成记忆卡片，每天过一遍（5 分钟），3 天后再进入启保停电路学习，能显著降低挫败感。", "category": "method", "priority": "high", "is_read": 0, "days": -3},
    {"title": "复习建议：安全规范每周一测", "content": "安全操作规范模块虽已通过，但属于长期记忆内容，建议每周一做 5 分钟速测保持记忆激活。", "category": "review", "priority": "medium", "is_read": 0, "days": -5},
    {"title": "练习推荐：跟练视频（0.75 倍速）", "content": "推荐 0.75 倍速跟练《启保停电路从零搭建》视频（12 分钟），跟做完成后再独立复现一遍，两遍正确率对比会写入学情档案。", "category": "practice", "priority": "medium", "is_read": 1, "days": -7},
    {"title": "保持节奏，别跳模块", "content": "检测到你曾尝试直接打开《传感器选型》（第 3 模块）。按当前画像建议按顺序推进，跳模块的正确率通常低于 40%，容易打击信心。", "category": "method", "priority": "low", "is_read": 1, "days": -10},
]

CATEGORY_LABELS = {"method": "方法建议", "resource": "资源推荐", "review": "复习建议", "practice": "练习推荐"}
PRIORITY_LABELS = {"high": "重要", "medium": "普通", "low": "可选"}


def _seed_student(
    student_id: str,
    target: str,
    progress: int,
    estimated_days: int,
    modules: list[dict],
    suggestions: list[dict],
) -> None:
    with get_session() as s:
        # 幂等：清旧数据（module/task 靠 cascade）
        old_paths = s.query(LearningPath).filter(LearningPath.student_id == student_id).all()
        for p in old_paths:
            s.delete(p)
        s.query(Suggestion).filter(Suggestion.student_id == student_id).delete()

        path = LearningPath(
            student_id=student_id,
            target=target,
            progress=progress,
            estimated_days=estimated_days,
            source="ai",
            version=1,
        )
        s.add(path)
        s.flush()

        for m in modules:
            module = LearningModule(
                path_id=path.path_id,
                name=m["name"],
                desc=m["desc"],
                progress=m["progress"],
                order_index=m["order_index"],
                status=m["status"],
                start_date=m["start"],
                end_date=m["end"],
                duration=m["duration"],
            )
            s.add(module)
            s.flush()
            for t in m["tasks"]:
                s.add(LearningTask(
                    module_id=module.module_id,
                    title=t["title"],
                    meta=t["meta"],
                    priority=t["priority"],
                    completed=t["completed"],
                    due_date=t["due"],
                ))

        for sg in suggestions:
            s.add(Suggestion(
                student_id=student_id,
                title=sg["title"],
                content=sg["content"],
                category=sg["category"],
                category_label=CATEGORY_LABELS[sg["category"]],
                priority=sg["priority"],
                priority_label=PRIORITY_LABELS[sg["priority"]],
                source="ai",
                is_read=sg["is_read"],
                read_at=_ts(sg["days"], 10, 30) if sg["is_read"] else None,
                created_at=_ts(sg["days"]),
            ))

    unread = sum(1 for x in suggestions if not x["is_read"])
    print(f"✅ {student_id}：路径 1 条（{len(modules)} 模块 / {sum(len(m['tasks']) for m in modules)} 任务）+ 建议 {len(suggestions)} 条（未读 {unread}）")


def main() -> None:
    _seed_student(
        "u001",
        target="工业机器人离线编程与路径规划 · 智能制造工程师认证备考",
        progress=45,
        estimated_days=60,
        modules=U001_MODULES,
        suggestions=U001_SUGGESTIONS,
    )
    _seed_student(
        "u002",
        target="工业机器人操作与编程基础达标（衔接实训岗位）",
        progress=20,
        estimated_days=90,
        modules=U002_MODULES,
        suggestions=U002_SUGGESTIONS,
    )
    print("完成：py -m backend.c_学习内容.seed_data")


if __name__ == "__main__":
    main()
