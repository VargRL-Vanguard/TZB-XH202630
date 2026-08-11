# 工作流程 14：Git 提交与 PR 流程（**4 人通用**）

> Git 操作是**最容易引发冲突**的地方，**严格按本流程**操作。
> 每个成员一个分支，**禁止**直接 push main。

---

## 分支策略

| 成员 | 分支名 | 目录 |
| --- | --- | --- |
| A | `feat/A-用户与聊天` | `1_用户与聊天/` + `公共/` |
| B | `feat/B-学情数据` | `2_学情数据/` |
| C | `feat/C-学习内容` | `3_学习内容/` |
| D | `feat/D-AI集成` | `4_AI集成/` + `prompts/` + `workflows/` |

**D 区** 特殊：负责 `prompts/` 和 `workflows/` 目录的合并（其他区可新增但 D 负责汇总）

---

## 步骤 1：开工前同步 main

**输入**：无

**操作**：
```bash
cd d:\TZB\TZB-XH202630
git checkout main
git pull origin main
git checkout feat/<你的区>
git merge main  # 把 main 的最新代码合并到自己分支
```

**输出**：自己分支已是最新

**验证**：
- [ ] `git log --oneline -5` 看到 main 的最新 commit
- [ ] 没有冲突

**失败处理**：合并冲突 → 群里 @ 队长，**不要**强推

---

## 步骤 2：完成任务后本地检查

**输入**：本任务的代码变更

**操作**：
```bash
# 1. 看改了什么
git status
git diff

# 2. 只 add 自己区的文件
git add backend/1_用户与聊天/  # A
git add backend/2_学情数据/    # B
git add backend/3_学习内容/    # C
git add backend/4_AI集成/      # D

# 3. 同时 add 自己那份任务清单
git add backend/任务清单_1_用户与聊天.md  # A
git add backend/任务清单_2_学情数据.md    # B
git add backend/任务清单_3_学习内容.md    # C
git add backend/任务清单_4_AI集成.md      # D
```

**输出**：暂存区只有自己区的文件

**验证**：
- [ ] `git status` 里**没有**其他区的文件
- [ ] `git status` 里**没有** `公共/`（除非是 A 区的任务）

**失败处理**：add 错文件 → `git restore --staged <file>`

---

## 步骤 3：commit（信息规范）

**输入**：暂存区内容

**操作**：
```bash
git commit -m "<任务ID> <一句话描述>

<详细说明（可选）>

Refs: <任务ID>"
```

**commit message 规范**：

✅ 正确：
- `A-00 自有数据层 + User 模型`
- `B-05 学情诊断 Agent + 单元测试`
- `C-04 领域专家 Agent + 3 种资源 prompt`
- `D-03 协同编排器 + retry 机制`

❌ 错误：
- `update`（太模糊）
- `fix bug`（没说清是什么 bug）
- `完成了一些东西`（没说明）

**输出**：1 个 commit

**验证**：
- [ ] commit message 以任务 ID 开头
- [ ] 描述清楚做了什么

**失败处理**：commit 信息错 → `git commit --amend -m "新信息"`

---

## 步骤 4：push 自己分支

**输入**：commit

**操作**：
```bash
git push origin feat/<你的区>
```

**输出**：自己分支已推送

**验证**：
- [ ] `git log origin/feat/<你的区> --oneline -1` 看到刚才的 commit

**失败处理**：push 失败 → 检查权限 / 联网

---

## 步骤 5：提 PR（合并到 main）

**输入**：推送的分支

**操作**：
1. 打开 GitHub 仓库
2. 点 "Compare & pull request"
3. **目标分支** = `main`
4. **源分支** = `feat/<你的区>`
5. **标题**：`[<任务ID>] <一句话描述>`
6. **描述**：
   ```markdown
   ## 任务
   - 任务 ID：A-00
   - 标题：自有数据层 + User 模型
   - 负责人：@A
   - 关联任务清单：backend/任务清单_1_用户与聊天.md#a-00

   ## 改动
   - 新增 backend/1_用户与聊天/db.py
   - 新增 backend/1_用户与聊天/models/user.py
   - 更新 backend/任务清单_1_用户与聊天.md（A-00 状态改为 ✅）

   ## 验证
   - [x] 本地跑通 quality_check（如果有）
   - [x] 单元测试全过
   - [x] 任务清单已更新

   ## 影响范围
   - 只影响 backend/1_用户与聊天/
   - 公共/ 未变更
   ```
7. 指定 reviewer = 队长 + 相关成员
8. 提交 PR

**输出**：1 个 PR

**验证**：
- [ ] PR 标题含任务 ID
- [ ] 描述含改动清单 + 验证清单 + 影响范围

**失败处理**：reviewer 没空 → 群里催，**不要**自己合并

---

## 步骤 6：响应 review

**输入**：reviewer 的评论

**操作**：
1. 收到 review 评论后**24 小时内**响应
2. 按评论修改代码
3. 重新 push（PR 自动更新）
4. 在评论下回复"已改"或解释原因

**输出**：1 个被接受的 PR

**验证**：
- [ ] 所有评论都有响应
- [ ] CI 通过（如有）

**失败处理**：与 reviewer 意见不合 → 群里讨论，**不要**吵

---

## 步骤 7：合并 + 删除分支

**输入**：被接受的 PR

**操作**：
1. PR review 通过后，由**队长**合并（"Squash and merge"）
2. 删除自己的特性分支：
   ```bash
   git checkout main
   git pull origin main
   git branch -d feat/<你的区>
   ```
3. 重新基于最新 main 拉新分支：
   ```bash
   git checkout -b feat/<你的区>  # 新分支从最新 main 开始
   ```

**输出**：分支已合并 + 新分支已建

**验证**：
- [ ] main 上能看到自己的 commit
- [ ] 旧分支已删

---

## 步骤 8：跨区协调（**关键**）

**输入**：发现需要改其他区的文件

**操作**：
1. **不要**在自己的分支改其他区
2. 群里提需求，说明：
   - 我需要改 `<其他区>/<文件>` 的 `<行/函数>`
   - 原因：...
3. 等对应成员同意后，由**他**在自己的分支改
4. 他合并到 main 后，你再 `git pull`

**输出**：1 份协调记录

**验证**：
- [ ] 变更经过对方同意
- [ ] 是对方的 commit，不是你的

**失败处理**：对方没空 → 群里升级，**不要**自己上

---

## 步骤 9：冲突处理

**输入**：合并时出现冲突

**操作**：
1. **不要** `git push --force`
2. **不要** `git rebase --skip`
3. 看冲突文件，手动解决：
   ```bash
   git status  # 看哪些文件冲突
   # 手动编辑冲突文件
   git add <冲突文件>
   git commit -m "merge: 解决与 main 的冲突"
   git push origin feat/<你的区>
   ```
4. 解决不了 → 群里 @ 队长

**输出**：1 个无冲突的 commit

**验证**：
- [ ] `git status` 没有 "both modified"
- [ ] CI 通过

**失败处理**：冲突太大 → reset 到 main 重新拉分支

---

## 步骤 10：每日同步

**输入**：每天开工前 / 下班前

**操作**：
```bash
# 早上开工
git checkout main
git pull origin main
git checkout feat/<你的区>
git merge main

# 下班前
git add .  # 仅自己区
git commit -m "..."
git push origin feat/<你的区>
```

**输出**：每天 2 次同步

**验证**：
- [ ] 群里每天 2 次汇报（早上 + 下班）
- [ ] 累计超过 2 天没 push → 群里提醒

---

## Git 验收清单

- [ ] 步骤 1：开工前已 merge main
- [ ] 步骤 2：只 add 自己区 + 任务清单
- [ ] 步骤 3：commit message 含任务 ID
- [ ] 步骤 4：push 自己分支（不直接 push main）
- [ ] 步骤 5：PR 描述含 改动 + 验证 + 影响
- [ ] 步骤 6：24 小时内响应 review
- [ ] 步骤 7：合并后删旧分支 + 拉新分支
- [ ] 步骤 8：跨区变更走协调
- [ ] 步骤 9：冲突手动解决（不 force）
- [ ] 步骤 10：每日 2 次同步

**违反任意一条 = Git 流程不合规 ❌**

---

## 禁止事项（**绝对不能做**）

| 禁止 | 原因 | 后果 |
| --- | --- | --- |
| `git push --force` 到 main | 覆盖他人代码 | **直接扣分 + 群里公开批评** |
| `git push --force` 到自己分支 | 丢失他人 review 历史 | 群里批评 |
| 直接 push main | 绕过 PR review | 群里批评 |
| 改其他区文件 | 制造冲突 | revert |
| `公共/` 改动不通知 | 影响所有人 | revert |
| commit 信息模糊 | 难以追溯 | 群里提醒重写 |
| 2 天没 push | 累积冲突风险 | 群里提醒 |
| `git reset --hard` 丢失工作 | 不可恢复 | 自负 |
