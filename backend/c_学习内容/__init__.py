"""c_学习内容/ — 成员 C 负责区

暴露给其他区（D / B）的对外契约：
- `from backend.c_学习内容.learning_path import save_ai_generated_path, get_overview, get_timeline, get_modules, get_tasks, handle_feedback`
- `from backend.c_学习内容.suggestions import save_ai_generated_suggestions, list_suggestions, mark_suggestion_read`
- `from backend.c_学习内容.agents import generate_resource`  # ⭐ 领域专家 Agent
- `from backend.c_学习内容.learning_path.renderers import render`  # ⭐ 3 个渲染器
"""

__version__ = "0.1.0"
