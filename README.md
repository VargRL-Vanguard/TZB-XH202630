# TZB-XH202630 — 领域知识个性化生成与多智能体协同决策系统

挑战杯 XH-202630 参赛项目。学情诊断 Agent + 领域专家 Agent + 审核裁判 Agent 三智能体协同，为学习者生成个性化学习路径与资源。

## 技术栈（重要：不是 PHP / WordPress）

| 层 | 技术 | 说明 |
|----|------|------|
| 后端 | **Python 3.11 + FastAPI** + SQLAlchemy | 四区模块化架构，单进程统一启动 |
| 前端 | **Vue 3 + TypeScript** + Vite + Element Plus | SPA，构建产物由 nginx 托管 |
| 数据库 | MySQL 8（生产）/ SQLite（本地单测兜底） | 四区各一个库 |
| AI | DeepSeek + 硅基流动（OpenAI 兼容协议） | 对话 / 路径 / 建议 / Embedding 四路 |
| 部署 | Docker Compose 或 本地直跑（二选一） | 见下文 |

> 本项目是 Python API 服务 + Vue 前端，**与 WordPress（PHP CMS）无任何关系**，不存在"WordPress 适配"问题。若需要额外挂一个 WordPress 官网页，用 nginx 不同端口/路径反代即可共存，不影响本系统。

## 目录结构

```
TZB-XH202630/
├── backend/                  # Python 后端（唯一后端，四区合一启动）
│   ├── main.py               #   启动入口：python -m backend.main
│   ├── a_用户与聊天/          #   A区：注册登录 / JWT鉴权 / 聊天 / WebSocket
│   ├── b_学情数据/            #   B区：学情诊断Agent / 知识库切片 / 测试画像
│   ├── c_学习内容/            #   C区：领域专家Agent / 学习路径 / 资源生成
│   ├── d_AI集成/             #   D区：审核裁判Agent / AI Provider / 对话编排
│   ├── 公共/                 #   共享：鉴权中间件 / 错误 / 日志 / 质量指标
│   ├── 概览.md               #   后端架构细节（四区职责/调用契约）
│   └── 协作协议.md            #   跨区调用规则
├── frontend/                 # Vue3 前端
│   ├── src/views/            #   13 个页面（仪表盘/学情/AI对话/质量看板…）
│   └── prompts/              #   前端交接文档 00~19 号
├── docker/                   # Dockerfile × 2 + entrypoint + MySQL 初始化 SQL
├── docker-compose.yml        # 一键容器化：mysql + backend(8000) + frontend(8080)
├── start_dev.ps1             # 一键本地直跑：backend(8000) + frontend(5173)
├── .env                      # 全部密钥（数据库/AI Key，已 gitignore，勿提交）
└── .env.example              # .env 模板（不含真实密钥）
```

更细的后端分层见 [backend/概览.md](backend/概览.md)；任务分工见 [backend/任务总看板.md](backend/任务总看板.md)。

## 启动方式（两种，不依赖 Docker）

### 方式 A：本地直跑（推荐调试用，无需 Docker）

前置：Python 3.11+、Node 18+、MySQL 8（四库需已建，见 `.env.example` 的 `*_DB_URL`）。

```powershell
# 1. 配置密钥（首次）
Copy-Item .env.example .env   # 然后编辑 .env 填 MySQL 密码与 AI Key

# 2. 一键启动（自动装依赖，拉起后端:8000 + 前端:5173 两个窗口）
.\start_dev.ps1
```

或手动分步：

```powershell
pip install -r backend/requirements.txt
python -m backend.a_用户与聊天.seed_data     # 种子数据（幂等）
python -m backend.main                        # 后端 :8000
cd frontend; npm install; npm run dev         # 前端 :5173
```

### 方式 B：Docker 一键容器化（推荐演示/部署用）

前置：Docker Desktop（WSL2 后端）。

```powershell
docker compose up -d --build
```

- 拓扑：`mysql(内网)` + `backend:8000` + `frontend:nginx:80→宿主8080`
- 访问入口：http://127.0.0.1:8080 （API/WS 同源反代，无需关心 8000）
- AI Key 与数据库密码通过 `env_file: .env` 注入容器，**不进镜像、不进 git**
- 容器每次重启自动重建表并刷新演示种子数据

## AI 服务配置（.env）

四个 AI 角色均走 OpenAI 兼容协议，只需 `.env`，改配置不用改代码：

| 角色 | 服务商 | 模型 | 环境变量前缀 |
|------|--------|------|--------------|
| ChatAI 辅导对话 | DeepSeek | deepseek-chat | `CHAT_AI_*` |
| PathAI 路径生成 | 硅基流动 | Qwen/Qwen2.5-7B-Instruct | `PATH_AI_*` |
| SuggestAI 学习建议 | 硅基流动（可切百炼） | Qwen/Qwen2.5-7B-Instruct | `SUGGEST_AI_*` |
| EmbedAI 向量检索 | 硅基流动 | BAAI/bge-m3 | `EMBED_AI_*` |

> Key 未配置时 AI 接口返回明确的 503 降级提示（前端有对应降级 UI），不会伪造回复。

## 测试账号（密码统一 `Test@1234`）

| 账号 | 角色 | 入口页 |
|------|------|--------|
| student001 | 学生 | 仪表盘 |
| teacher001 | 教师 | 学生列表 |
| admin001 | 管理员 | 质量看板 |

## 常见问题

- **页面全空态** → 种子数据未灌，执行方式 A 的 seed 命令（Docker 方式自动灌）
- **AI 对话报"未配置"** → 检查 `.env` 的 `CHAT_AI_API_KEY`；Docker 方式需 `docker compose up -d` 重建容器使 env_file 生效
- **想加新页面** → 看 `frontend/prompts/14_交接手册_搭积木总览.md`
- **后端接口契约** → `http://127.0.0.1:8000/docs`（Swagger）或 `frontend/prompts/08_接口契约速查表_字段级.md`
