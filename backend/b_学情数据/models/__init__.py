"""
B 区 ORM 模型包。
按表分文件，所有模型都继承自本模块的 Base。
"""
from backend.b_学情数据.models.base import Base  # noqa: F401
from backend.b_学情数据.models.student import Student  # noqa: F401
from backend.b_学情数据.models.activity import Activity  # noqa: F401
from backend.b_学情数据.models.kb_chunk import KbChunk  # noqa: F401
from backend.b_学情数据.models.test_profile import TestProfile  # noqa: F401
from backend.b_学情数据.models.diagnosis_record import DiagnosisRecord  # noqa: F401
