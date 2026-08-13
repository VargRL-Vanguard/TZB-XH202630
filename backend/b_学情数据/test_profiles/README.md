# 测试画像集（B-07 夺奖专项）

> **领域**：智能制造-工业机器人与PLC应用
> **用途**：学情诊断 Agent（B-05）的验收输入 + A-05 端到端"画像-难度适配准确率"指标计算 + 演示视频主角数据源
> **关联任务**：[B-07 测试画像](../../任务清单_b_学情数据.md#b-07)
> **知识点来源**：[kp_taxonomy.json](../kb/kp_taxonomy.json)（6 模块 42 个知识点）

---

## 1. 3 组画像差异点对比

| 画像 | 背景 | 理论测试分 | 强知识（strongKPs） | 弱知识（weakKPs） | 交互目标 |
| --- | --- | --- | --- | --- | --- |
| **p-001 本科应届生** | 智能制造工程本科，理论扎实 | 82 | kp01/kp02/kp03/kp15（4 个） | kp12d/kp22c（2 个，severity 偏 low/medium） | 深入离线编程与路径规划，备考智能制造工程师认证 |
| **p-002 高职在读生** | 工业机器人技术高职，基础薄弱 | 58 | kp01（1 个） | kp12/kp12c/kp22/kp22a/kp04c/kp05b（6 个，3 个 high） | 从基础补起，获取适合高职层次的入门资源 |
| **p-003 企业转岗人员** | 机械设计制造本科，5 年实战经验跨领域转岗 | 55 | kp01d/kp04/kp06b（3 个，均为实操型） | kp03/kp22/kp22b/kp05/kp05a/kp12c（6 个，2 个 high） | 补齐 PLC 编程与工业通信理论，转型系统集成岗位 |

**差异显著性说明**：

- **学历层次**：本科 / 高职 / 本科（但跨领域）三组覆盖了"高理论-低实战""低理论-低实战""低理论-高实战"三种典型组合。
- **理论分跨度**：82 → 58 → 55，最高与最低相差 **27 分**，满足 ≥15 分差异显著性要求。
- **强弱知识数量对比**：画像 1 strong(4) > weak(2)；画像 2 weak(6) >> strong(1)；画像 3 weak(6) > strong(3) 但 strong 全部为实操型。
- **活动得分分布**：画像 1 多数 80+；画像 2 多数 40-65；画像 3 实操 75-90 / 理论 42-55，呈"两极分化"特征。

---

## 2. 目录结构

```
backend/b_学情数据/test_profiles/
├── profile_01_本科应届生.json          # 画像 1 完整输入
├── profile_02_高职在读生.json          # 画像 2 完整输入
├── profile_03_企业转岗人员.json        # 画像 3 完整输入
├── expected_outputs/
│   ├── profile_01_expected.json       # 画像 1 人工标注预期弱知识
│   ├── profile_02_expected.json       # 画像 2 人工标注预期弱知识
│   └── profile_03_expected.json       # 画像 3 人工标注预期弱知识
├── README.md                          # 本文件
├── ../scripts/load_test_profiles.py   # 一键导入脚本
└── ../tests/test_profiles.py          # 单测
```

---

## 3. 画像 JSON Schema

每个画像 JSON 必须包含以下顶层字段：

```json
{
  "profile_id": "p-001",
  "label": "本科应届生",
  "learnerProfile": {
    "education": "本科",
    "major": "智能制造工程",
    "theoryTestScore": 82,
    "weakKPs": ["kp12d", "kp22c"],
    "strongKPs": ["kp01", "kp02", "kp03", "kp15"]
  },
  "activityHistory": [
    {
      "activityType": "test",
      "resourceName": "工业机器人坐标系单元测试",
      "status": "completed",
      "progress": 100,
      "score": 85,
      "kpTags": ["kp02", "kp12"],
      "startTime": "2026-08-12T14:30:00",
      "durationMinutes": 45
    }
  ],
  "interactionGoal": "希望深入学习工业机器人离线编程与路径规划，准备智能制造工程师认证"
}
```

**字段约束**：
- `profile_id`：主键，格式 `p-00X`
- `learnerProfile.theoryTestScore`：0-100 整数
- `learnerProfile.weakKPs` / `strongKPs`：kp_id 数组，必须来自 `kp_taxonomy.json`
- `activityHistory`：最近 14 天 8-10 条活动记录
- `activityHistory[].kpTags`：也必须来自 `kp_taxonomy.json` 的合法 kp_id

---

## 4. 使用方法

### 4.1 加载画像 JSON（Python 读取）

```python
import json
from pathlib import Path

profiles_dir = Path("backend/b_学情数据/test_profiles")

# 读取单个画像
with open(profiles_dir / "profile_01_本科应届生.json", encoding="utf-8") as f:
    profile = json.load(f)

# 读取预期输出
with open(profiles_dir / "expected_outputs" / "profile_01_expected.json", encoding="utf-8") as f:
    expected = json.load(f)
```

### 4.2 一键导入到数据库

```bash
# 方式 1：模块方式运行（推荐，项目根目录下）
python -m backend.b_学情数据.scripts.load_test_profiles

# 方式 2：直接运行脚本
python backend/b_学情数据/scripts/load_test_profiles.py
```

脚本会将 3 个画像 JSON upsert 到 `test_profile` 表（`profile_id` 存在则更新），同时把对应的 `expected_weak_kps` 写入 `expected_weak_kps` 字段。

### 4.3 跑学情诊断（diagnose）并对比预期输出

```python
import asyncio
from backend.b_学情数据.analytics import diagnose

# 1. 先用 load_test_profiles.py 把画像入库
# 2. （需配合 A 区 learner_profile 或 mock）调用 diagnose
result = asyncio.run(diagnose("p-001"))

# 3. 与 expected_outputs 对比
#    - weakKPs 是否覆盖 expected_weak_kps 中的 kp_id
#    - confidence 是否落在 expected_confidence_range
#    - knowledgeGaps 数量是否落在 expected_gap_count_range
```

### 4.4 对比 expected 输出（A-05 quality_check 视角）

```python
# expected_weak_kps 中的 kp_id 应全部出现在 diagnose 结果的 weakKPs 或 knowledgeGaps 中
# expected_strong_kps 应全部出现在 diagnose 结果的 strongKPs 中
# confidence 应落在 expected_confidence_range [low, high] 区间内
# len(knowledgeGaps) 应落在 expected_gap_count_range [low, high] 区间内
```

---

## 5. 每个画像的预期诊断结果说明

### 5.1 画像 1（p-001 本科应届生）预期诊断结果

本科应届生画像的理论测试分为 82 分，属于理论扎实的强画像类型。该学生主修智能制造工程专业，在工业机器人基础（kp01）、坐标系（kp02）、PLC 编程基础（kp03）以及路径规划（kp15）四个核心知识点上表现突出，活动历史中这些知识点的得分普遍在 80-92 分之间，形成了明确的强知识簇。预期诊断 Agent 应能精准识别这 4 个 strongKPs，并给出较高的置信度（预计落在 0.70-0.90 区间）。弱知识方面，该学生仅在 D-H 参数法建模（kp12d，severity=medium）和顺控程序 SFC 概念（kp22c，severity=low）两个进阶知识点上存在不足，活动数据中相关得分分别为 78 分和 68 分，与画像标注高度一致。预期 knowledgeGaps 数量为 2-5 个，整体呈现"强知识多、弱知识少且 severity 偏低"的健康画像特征。该画像主要用于验证诊断 Agent 在"高理论分学生"场景下不会误判强知识为弱知识，同时能精准捕获进阶难点。交互目标是深入离线编程与路径规划，备考智能制造工程师认证，因此后续资源推荐应聚焦 kp18/kp15a 等高阶知识点。

### 5.2 画像 2（p-002 高职在读生）预期诊断结果

高职在读生画像的理论测试分仅为 58 分，是三组画像中理论基础最薄弱的一组。该学生主修工业机器人技术专业，仅在工业机器人基础（kp01）一个知识点上具备一定基础（活动得分 70 分），其余知识点普遍得分偏低。预期诊断 Agent 应识别出至少 4 个 high/medium 级别的弱知识盲区，其中坐标系变换（kp12，得分 48 分）、逆运动学概念（kp12c，得分 52 分）和模拟量信号处理（kp22，得分 45 分）三个知识点 severity 应为 high，梯形图编程（kp22a，得分 58 分）、编码器原理（kp04c，未完成无得分）和工业以太网（kp05b，得分 50 分）severity 应为 medium。预期 knowledgeGaps 数量为 4-8 个，置信度预计落在 0.60-0.80 区间（因活动数据充足但得分一致性高，置信度不会过低）。该画像的核心价值在于验证诊断 Agent 对"大面积弱知识"场景的覆盖能力：既要保证 weakKPs 数量充足（≥4），又要避免因弱知识过多而将唯一强知识 kp01 误判为弱知识。交互目标是从基础补起，后续资源推荐应侧重 level 1-2 的入门级内容，避免推荐 level 3 的进阶知识点。

### 5.3 画像 3（p-003 企业转岗人员）预期诊断结果

企业转岗人员画像是三组中最具挑战性和演示价值的画像，其核心特征是"实操强、理论弱"的两极分化。该学生拥有机械设计制造及其自动化本科学历和 5 年行业实战经验，在机器人本体结构（kp01d，得分 90 分）、传感器选型（kp04，得分 85 分）和气动执行元件（kp06b，得分 88 分）三个实操型知识点上表现优异，但在 PLC 工作原理（kp03，得分 48 分）和模拟量信号处理理论（kp22，得分 42 分）上严重不足，severity 应为 high。此外，STL/ST 文本编程（kp22b，未完成）、工业通信网络分层（kp05，得分 50 分）和 Modbus 协议（kp05a，实操 75 分但理论不足）severity 应为 medium。值得注意的是，kp05a 在实操中得分 75 分但理论测试偏低，诊断 Agent 需要综合画像标注（weakKPs 含 kp05a）和活动数据做出判断，这考验了算法在"实操与理论不一致"场景下的鲁棒性。预期 knowledgeGaps 数量为 3-7 个，置信度预计落在 0.60-0.85 区间。该画像的交互目标是转型智能制造系统集成岗位，后续资源推荐应针对理论短板提供"理论+实操对照"型资源，而非纯理论或纯实操内容。该画像也是演示视频的首选主角，因其跨领域背景最具故事性。

---

## 6. 版权声明

本测试画像集为 XH-202630 挑战杯参赛项目「领域知识个性化生成与多智能体协同决策系统研究」的内部测试数据，由项目 B 区（学情数据）团队编制。

- **许可范围**：仅限本项目内部使用，用于学情诊断 Agent 验收、A-05 端到端质量检查及演示视频制作。
- **数据来源**：所有知识点 ID（kp_id）均来自 `backend/b_学情数据/kb/kp_taxonomy.json` 中定义的知识体系（6 模块 42 个知识点）。画像中的人名、背景为虚构测试数据，不涉及真实个人信息。
- **引用规范**：如需在论文或汇报中引用本数据集，请注明来源为"XH-202630 挑战杯项目 B-07 测试画像集"。
- **修改约束**：修改画像 JSON 后必须同步更新 `expected_outputs/` 下的预期输出文件，并重新运行 `tests/test_profiles.py` 确保单测通过。
