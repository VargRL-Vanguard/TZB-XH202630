"""
公共区统一导出。
B/C/D 都可以：
    from backend.公共 import response, logger, errors, config, metrics
    from backend.公共.errors import AuthError, QualityError
"""
# 注意：必须直接 import 子模块，不能 `from backend.公共 import ...`
# 否则会在本 __init__.py 内部形成循环引用（pytest 收集时容易出 bug）
from backend.公共 import response, logger, errors, config, metrics  # noqa: F401
from backend.公共 import auth_middleware  # noqa: F401  # S-02: get_current_user / require_auth / require_role
