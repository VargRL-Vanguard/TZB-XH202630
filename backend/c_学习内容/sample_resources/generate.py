"""C-08 3 套脱敏样例资源生成脚本。

运行：
    cd backend
    python c_学习内容/sample_resources/generate.py

注：项目目录名以 c_/数字 开头，无法用标准 import 加载。
本脚本通过 importlib 把模块挂到虚拟包 `c_pkg` 下，让 `from .X import Y` 工作。
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import types

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(OUTPUT_DIR, "..", ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
# 让绝对导入 `from backend.公共...` 能工作
for p in (BACKEND_DIR, PROJECT_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)


def _load_in_pkg(pkg: types.ModuleType, name: str, path: str) -> types.ModuleType:
    full = f"{pkg.__name__}.{name}"
    spec = importlib.util.spec_from_file_location(full, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[full] = mod
    setattr(pkg, name, mod)
    spec.loader.exec_module(mod)
    return mod


def _make_pkg(name: str, dir_path: str) -> types.ModuleType:
    """创建一个具有 __path__ / __file__ 的虚拟包（让 from .X import Y 能正常工作）。"""
    pkg = types.ModuleType(name)
    pkg.__path__ = [dir_path]
    init_path = os.path.join(dir_path, "__init__.py")
    if os.path.exists(init_path):
        pkg.__file__ = init_path
    sys.modules[name] = pkg
    return pkg


def _exec_as_pkg(pkg: types.ModuleType, init_path: str) -> types.ModuleType:
    """将 __init__.py 加载为 pkg 自身（沿用 pkg 的 __path__/__file__），让 from .X import Y 走 sys.modules。"""
    spec = importlib.util.spec_from_file_location(pkg.__name__, init_path, submodule_search_locations=pkg.__path__)
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__.update(pkg.__dict__)
    mod.__name__ = pkg.__name__
    mod.__path__ = pkg.__path__
    mod.__file__ = init_path
    mod.__package__ = pkg.__name__
    sys.modules[pkg.__name__] = mod
    spec.loader.exec_module(mod)
    # 把 mod 上的属性回写到原 pkg
    for k, v in mod.__dict__.items():
        if not k.startswith("_") or k in ("__all__",):
            setattr(pkg, k, v)
    return pkg


# C 区目录名（兼容历史别名 3_学习内容 — 旧 docstring 引用）
_C_AREA_DIR = os.environ.get("C_AREA_DIR", "c_学习内容")


def _import_via_path():
    base = os.path.join(BACKEND_DIR, _C_AREA_DIR)

    # 虚拟包
    pkg = _make_pkg("c_pkg", base)
    setattr(pkg, "config", _load_in_pkg(pkg, "config", os.path.join(base, "config.py")))
    _load_in_pkg(pkg, "db", os.path.join(base, "db.py"))

    # models 子包：先把所有子模块预加载好，再加载 __init__.py 让 from .X import Y 走 sys.modules
    models_pkg = _make_pkg("c_pkg.models", os.path.join(base, "models"))
    setattr(pkg, "models", models_pkg)
    _load_in_pkg(models_pkg, "base", os.path.join(base, "models", "base.py"))
    _load_in_pkg(models_pkg, "learning_path", os.path.join(base, "models", "learning_path.py"))
    _load_in_pkg(models_pkg, "suggestion", os.path.join(base, "models", "suggestion.py"))
    _load_in_pkg(models_pkg, "resource", os.path.join(base, "models", "resource.py"))
    _load_in_pkg(models_pkg, "resource_version", os.path.join(base, "models", "resource_version.py"))
    _load_in_pkg(models_pkg, "interaction_log", os.path.join(base, "models", "interaction_log.py"))
    # 把 __init__.py 加载为 c_pkg.models 本身（替换占位模块），触发 from .X import Y
    _exec_as_pkg(models_pkg, os.path.join(base, "models", "__init__.py"))

    # 建表
    from c_pkg.models.base import Base
    from c_pkg.db import engine
    Base.metadata.create_all(bind=engine)

    # agents 子包
    agents_pkg = _make_pkg("c_pkg.agents", os.path.join(base, "agents"))
    setattr(pkg, "agents", agents_pkg)
    _load_in_pkg(agents_pkg, "expert_prompts", os.path.join(base, "agents", "expert_prompts.py"))
    _load_in_pkg(agents_pkg, "resource_factory", os.path.join(base, "agents", "resource_factory.py"))
    _load_in_pkg(agents_pkg, "kp_coverage_check", os.path.join(base, "agents", "kp_coverage_check.py"))
    _load_in_pkg(agents_pkg, "expert_agent", os.path.join(base, "agents", "expert_agent.py"))
    # 触发 agents/__init__.py（让 from c_pkg.agents import generate_resource 可用）
    _exec_as_pkg(agents_pkg, os.path.join(base, "agents", "__init__.py"))

    # learning_path 子包（先建包，再建 renderers）
    rp_pkg = _make_pkg("c_pkg.learning_path", os.path.join(base, "learning_path"))
    setattr(pkg, "learning_path", rp_pkg)
    _exec_as_pkg(rp_pkg, os.path.join(base, "learning_path", "__init__.py"))

    renderers_pkg = _make_pkg("c_pkg.learning_path.renderers", os.path.join(base, "learning_path", "renderers"))
    setattr(rp_pkg, "renderers", renderers_pkg)
    _load_in_pkg(renderers_pkg, "customized_resource", os.path.join(base, "learning_path", "renderers", "customized_resource.py"))
    _load_in_pkg(renderers_pkg, "practice_guide", os.path.join(base, "learning_path", "renderers", "practice_guide.py"))
    _load_in_pkg(renderers_pkg, "tiered_quiz", os.path.join(base, "learning_path", "renderers", "tiered_quiz.py"))
    # 加载 renderers/__init__.py 让 from . import X 等语句生效
    _exec_as_pkg(renderers_pkg, os.path.join(base, "learning_path", "renderers", "__init__.py"))

    from c_pkg.agents import generate_resource, DiagnosisResult
    from c_pkg.learning_path.renderers import render
    return generate_resource, DiagnosisResult, render


# 脱敏后 3 组画像
THREE_PROFILES = [
    {
        "name": "基础薄弱组",
        "studentId": "demo-weak-001",
        "weakKPs": ["kp_python_basics", "kp_control_flow"],
        "difficulty": 1,
    },
    {
        "name": "中等进阶组",
        "studentId": "demo-mid-002",
        "weakKPs": ["kp_function_design", "kp_oop_basics"],
        "difficulty": 3,
    },
    {
        "name": "高阶突破组",
        "studentId": "demo-strong-003",
        "weakKPs": ["kp_async_programming", "kp_design_patterns"],
        "difficulty": 5,
    },
]


def _save(filename: str, content: str):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✓ {filename} ({len(content):,} bytes)")


def main():
    os.makedirs(os.path.join(OUTPUT_DIR, "screenshots"), exist_ok=True)
    print("=" * 60)
    print("C-08 脱敏样例生成")
    print("=" * 60)

    generate_resource, DiagnosisResult, render = _import_via_path()

    profile = THREE_PROFILES[1]  # 中等组
    diag = DiagnosisResult(
        studentId=profile["studentId"],
        weakKPs=profile["weakKPs"],
        knowledgeGaps=profile["weakKPs"],
        recommendedDifficulty=profile["difficulty"],
    )

    # 1. 定制化资源
    print(f"\n[1/3] 生成 customized_resource（{profile['name']}）...")
    cr = generate_resource(profile["studentId"], diag, "customized_resource", trigger_reason="demo_sample")
    out = render({
        "type": "customized_resource",
        "structured_content": cr.content,
        "title": cr.title,
        "difficulty": cr.difficulty,
        "version": 1,
        "kp_coverage": cr.kp_coverage,
        "cited_chunks": cr.cited_chunks,
        "resource_id": cr.resource_id,
    })
    _save("customized_resource_sample.html", _wrap_html(out["html"], cr.title, "customized_resource"))
    _save("customized_resource_sample.md", out["markdown"])
    _save("customized_resource_sample.json", json.dumps(json.loads(cr.model_dump_json()), ensure_ascii=False, indent=2))

    # 2. 实操指南
    print(f"\n[2/3] 生成 practice_guide（{profile['name']}）...")
    pg = generate_resource(profile["studentId"], diag, "practice_guide", trigger_reason="demo_sample")
    out = render({
        "type": "practice_guide",
        "structured_content": pg.content,
        "title": pg.title,
        "difficulty": pg.difficulty,
        "version": 1,
        "kp_coverage": pg.kp_coverage,
        "cited_chunks": pg.cited_chunks,
        "resource_id": pg.resource_id,
    })
    _save("practice_guide_sample.html", _wrap_html(out["html"], pg.title, "practice_guide"))
    _save("practice_guide_sample.md", out["markdown"])
    _save("practice_guide_sample.json", json.dumps(json.loads(pg.model_dump_json()), ensure_ascii=False, indent=2))

    # 3. 分阶测试题
    print(f"\n[3/3] 生成 tiered_quiz（{profile['name']}）...")
    tq = generate_resource(profile["studentId"], diag, "tiered_quiz", trigger_reason="demo_sample")
    out = render({
        "type": "tiered_quiz",
        "structured_content": tq.content,
        "title": tq.title,
        "difficulty": tq.difficulty,
        "version": 1,
        "kp_coverage": tq.kp_coverage,
        "cited_chunks": tq.cited_chunks,
        "resource_id": tq.resource_id,
    })
    _save("tiered_quiz_sample.html", _wrap_html(out["html"], tq.title, "tiered_quiz"))
    _save("tiered_quiz_sample.md", out["markdown"])
    _save("tiered_quiz_sample.json", json.dumps(json.loads(tq.model_dump_json()), ensure_ascii=False, indent=2))

    print("\n✓ 3 套脱敏样例生成完成")
    print(f"  输出目录: {OUTPUT_DIR}")


def _wrap_html(body: str, title: str, kind: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}（{kind}）- 脱敏样例 - C-08</title>
</head>
<body>
{body}
<footer style="text-align:center;color:#9ca3af;font-size:12px;padding:24px">
  C-08 脱敏样例 · {kind} · 生成于 XH-202630 挑战杯项目
</footer>
</body>
</html>
"""


if __name__ == "__main__":
    main()
