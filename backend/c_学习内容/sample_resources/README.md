# C-08 脱敏样例资源

> **任务**：C-08 演示视频用的 3 套脱敏样例资源（**9-5 必交**）
> **使用方**：D-08 演示视频脚本（10 分钟）必展示 3 套样例
> **生成时间**：由 `generate.py` 脚本生成

---

## 脱敏声明

**本目录下所有样例均经过脱敏处理**：
- 所有 `studentId` 已替换为 `demo-weak-001` / `demo-mid-002` / `demo-strong-003`
- 不含真实姓名、学号、邮箱、班级、学院等任何可识别学生身份的信息
- 知识库切片 ID（`cited_chunks`）为 mock 标识符，不对应真实学情数据
- 选用画像为脱敏的 3 组测试画像（基础薄弱 / 中等进阶 / 高阶突破），**保证可复现**

如果本目录被误提交真实数据，请立即联系 C 区负责人并按 `协作协议 §9` 处理。

---

## 选用画像

| 组别 | studentId | 弱项 kp | 推荐难度 | 用途 |
| --- | --- | --- | --- | --- |
| 基础薄弱组 | demo-weak-001 | `kp_python_basics`, `kp_control_flow` | 1/5 | 演示降维解释 |
| 中等进阶组 | demo-mid-002 | `kp_function_design`, `kp_oop_basics` | 3/5 | **本次样例使用** |
| 高阶突破组 | demo-strong-003 | `kp_async_programming`, `kp_design_patterns` | 5/5 | 演示进阶挑战 |

**本次生成采用「中等进阶组」**（最全面，能展示 3 种形态资源的标准效果）。

---

## 3 套样例清单

| 文件 | 类型 | 用途 |
| --- | --- | --- |
| `customized_resource_sample.html` | 定制化讲义 | 演示视频讲义展示 |
| `practice_guide_sample.html` | 实操指南 | 演示视频操作流程展示 |
| `tiered_quiz_sample.html` | 分阶测试题 | 演示视频交互测试展示 |
| `*_sample.md` | Markdown 源 | 备用导出 |
| `*_sample.json` | 结构化数据 | 调试 / 回放 |
| `screenshots/` | 截图占位 | 演示视频用，**录制前用 Playwright 截** |
| `generate.py` | 生成脚本 | 复现用 |

---

## 重新生成

```bash
cd backend
python c_学习内容/sample_resources/generate.py
```

---

## 截图清单（演示视频前补齐）

| 编号 | 内容 | 路径 | 状态 |
| --- | --- | --- | --- |
| SS-01 | 定制化讲义（首屏） | `screenshots/customized_resource_top.png` | ⬜ 待 Playwright 截 |
| SS-02 | 定制化讲义（代码块高亮） | `screenshots/customized_resource_code.png` | ⬜ 待 Playwright 截 |
| SS-03 | 实操指南（步骤展开） | `screenshots/practice_guide_steps.png` | ⬜ 待 Playwright 截 |
| SS-04 | 分阶测试题（题目 + 难度徽章） | `screenshots/tiered_quiz_questions.png` | ⬜ 待 Playwright 截 |
| SS-05 | 分阶测试题（解析折叠） | `screenshots/tiered_quiz_explanation.png` | ⬜ 待 Playwright 截 |

---

## 硬指标自检（生成时已跑过）

| 指标 | 目标 | 状态 |
| --- | --- | --- |
| 幻觉率 | < 0.05 | ✅ mock 兜底达标 |
| 核心知识点覆盖率 | ≥ 0.90 | ✅ mock 兜底达标 |
| 画像-难度适配准确率 | ≥ 0.85 | ✅ mock 兜底达标 |

> 实际值由 mock 兜底（在 B-06 知识库就绪前为演示用）；A-05 跑通后由真实指标覆盖。
