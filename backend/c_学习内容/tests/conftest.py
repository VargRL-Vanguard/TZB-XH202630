"""C 区测试共置：每个测试用独立 SQLite in-memory + 虚拟包加载。

由于项目目录以数字开头（`1_用户与聊天/`、`2_学情数据/` 等），无法用标准 import。
本 conftest 用 `_load_c_package()` 构造虚拟包 `c_pkg`，让 `from c_pkg.X import Y` 工作。
"""
from __future__ import annotations

import importlib
import importlib.util
import os
import sys
import tempfile
import types
from contextlib import contextmanager


# ---------------------------------------------------------------------------
# 把 c_学习内容 加入 sys.path，使测试文件可 `from tests.conftest import ...`
# ---------------------------------------------------------------------------

_C_AREA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _C_AREA_DIR not in sys.path:
    sys.path.insert(0, _C_AREA_DIR)


# ---------------------------------------------------------------------------
# 虚拟包加载（与 sample_resources/generate.py 共享思路）
# ---------------------------------------------------------------------------

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _make_pkg(name: str, dir_path: str) -> types.ModuleType:
    pkg = types.ModuleType(name)
    pkg.__path__ = [dir_path]
    init_path = os.path.join(dir_path, "__init__.py")
    if os.path.exists(init_path):
        pkg.__file__ = init_path
    sys.modules[name] = pkg
    return pkg


def _load_in_pkg(pkg: types.ModuleType, name: str, path: str) -> types.ModuleType:
    full = f"{pkg.__name__}.{name}"
    spec = importlib.util.spec_from_file_location(full, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[full] = mod
    setattr(pkg, name, mod)
    spec.loader.exec_module(mod)
    return mod


def _exec_as_pkg(pkg: types.ModuleType, init_path: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(pkg.__name__, init_path, submodule_search_locations=pkg.__path__)
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__.update(pkg.__dict__)
    mod.__name__ = pkg.__name__
    mod.__path__ = pkg.__path__
    mod.__file__ = init_path
    mod.__package__ = pkg.__name__
    sys.modules[pkg.__name__] = mod
    spec.loader.exec_module(mod)
    for k, v in mod.__dict__.items():
        if not k.startswith("_") or k in ("__all__",):
            setattr(pkg, k, v)
    return pkg


def _load_c_package():
    """加载 C 区所有模块到 `c_pkg` 虚拟包，返回 (generate_resource, DiagnosisResult, VALID_TYPES, render)。"""
    base = os.path.join(BACKEND_DIR, "c_学习内容")

    pkg = _make_pkg("c_pkg", base)
    _load_in_pkg(pkg, "config", os.path.join(base, "config.py"))
    _load_in_pkg(pkg, "db", os.path.join(base, "db.py"))

    # models
    models_pkg = _make_pkg("c_pkg.models", os.path.join(base, "models"))
    setattr(pkg, "models", models_pkg)
    _load_in_pkg(models_pkg, "base", os.path.join(base, "models", "base.py"))
    _load_in_pkg(models_pkg, "learning_path", os.path.join(base, "models", "learning_path.py"))
    _load_in_pkg(models_pkg, "suggestion", os.path.join(base, "models", "suggestion.py"))
    _load_in_pkg(models_pkg, "resource", os.path.join(base, "models", "resource.py"))
    _load_in_pkg(models_pkg, "resource_version", os.path.join(base, "models", "resource_version.py"))
    _load_in_pkg(models_pkg, "interaction_log", os.path.join(base, "models", "interaction_log.py"))
    _exec_as_pkg(models_pkg, os.path.join(base, "models", "__init__.py"))

    # agents
    agents_pkg = _make_pkg("c_pkg.agents", os.path.join(base, "agents"))
    setattr(pkg, "agents", agents_pkg)
    _load_in_pkg(agents_pkg, "expert_prompts", os.path.join(base, "agents", "expert_prompts.py"))
    _load_in_pkg(agents_pkg, "resource_factory", os.path.join(base, "agents", "resource_factory.py"))
    _load_in_pkg(agents_pkg, "kp_coverage_check", os.path.join(base, "agents", "kp_coverage_check.py"))
    _load_in_pkg(agents_pkg, "expert_agent", os.path.join(base, "agents", "expert_agent.py"))
    _exec_as_pkg(agents_pkg, os.path.join(base, "agents", "__init__.py"))

    # learning_path
    rp_pkg = _make_pkg("c_pkg.learning_path", os.path.join(base, "learning_path"))
    setattr(pkg, "learning_path", rp_pkg)
    for sub in ("service", "overview", "timeline", "modules", "tasks", "feedback_adapter", "feedback"):
        f = os.path.join(base, "learning_path", f"{sub}.py")
        if os.path.exists(f):
            _load_in_pkg(rp_pkg, sub, f)
    _exec_as_pkg(rp_pkg, os.path.join(base, "learning_path", "__init__.py"))

    renderers_pkg = _make_pkg("c_pkg.learning_path.renderers", os.path.join(base, "learning_path", "renderers"))
    setattr(rp_pkg, "renderers", renderers_pkg)
    _load_in_pkg(renderers_pkg, "customized_resource", os.path.join(base, "learning_path", "renderers", "customized_resource.py"))
    _load_in_pkg(renderers_pkg, "practice_guide", os.path.join(base, "learning_path", "renderers", "practice_guide.py"))
    _load_in_pkg(renderers_pkg, "tiered_quiz", os.path.join(base, "learning_path", "renderers", "tiered_quiz.py"))
    _exec_as_pkg(renderers_pkg, os.path.join(base, "learning_path", "renderers", "__init__.py"))

    # suggestions
    sg_pkg = _make_pkg("c_pkg.suggestions", os.path.join(base, "suggestions"))
    setattr(pkg, "suggestions", sg_pkg)
    for sub in ("service", "list", "read"):
        f = os.path.join(base, "suggestions", f"{sub}.py")
        if os.path.exists(f):
            _load_in_pkg(sg_pkg, sub, f)
    _exec_as_pkg(sg_pkg, os.path.join(base, "suggestions", "__init__.py"))

    from c_pkg.agents import generate_resource, DiagnosisResult, VALID_TYPES
    from c_pkg.learning_path.renderers import render
    return generate_resource, DiagnosisResult, VALID_TYPES, render


# 在 import 时立刻把 c_pkg 加载好，让各测试文件可以直接 import
_generate_resource, DiagnosisResult, _VALID_TYPES, render = _load_c_package()


# ---------------------------------------------------------------------------
# 隔离 DB fixture
# ---------------------------------------------------------------------------

def _sqlite_url() -> str:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return f"sqlite:///{path}"


@contextmanager
def isolated_db():
    """为单测构造独立的 C 区 SQLite 数据库（每个测试一个新 db）。"""
    url = _sqlite_url()
    os.environ["LEARNING_CONTENT_DB_URL"] = url
    # 重新加载 config / db
    importlib.reload(sys.modules["c_pkg.config"])
    importlib.reload(sys.modules["c_pkg.db"])
    from c_pkg.models.base import Base
    Base.metadata.create_all(bind=sys.modules["c_pkg.db"].engine)
    try:
        yield sys.modules["c_pkg.db"], Base
    finally:
        # 关闭 + dispose engine，避免 ResourceWarning（unclosed sqlite3.Connection）
        try:
            sys.modules["c_pkg.db"].engine.dispose()
        except Exception:
            pass
        # 清掉临时 db 文件
        try:
            os.unlink(url.replace("sqlite:///", ""))
        except Exception:
            pass
