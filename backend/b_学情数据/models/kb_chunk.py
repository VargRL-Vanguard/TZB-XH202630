"""
KbChunk 表：知识库切片（挑战杯新增 ⭐）。

B-06 验收标准强制字段：
  chunk_id (PK) / doc_id / content / embedding (vector 或 JSON)
  / kp_tags (JSON 数组) / source_url / version
"""
from sqlalchemy import String, Text, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column

from backend.b_学情数据.models.base import Base, TimestampMixin


class KbChunk(Base, TimestampMixin):
    """
    垂直领域知识库切片表。
    MVP 阶段 embedding 存 JSON（list[float]），后续换 pgvector 再迁移。
    """

    __tablename__ = "kb_chunk"

    # 主键：c-00001 递增或雪花
    chunk_id: Mapped[str] = mapped_column(
        String(64), primary_key=True, comment="切片ID（PK）"
    )

    # 属于哪个原始文档
    doc_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default="", index=True, comment="所属文档ID"
    )

    # 切片正文（200-500 字）
    content: Mapped[str] = mapped_column(
        Text, nullable=False, default="", comment="切片正文"
    )

    # 向量嵌入：MVP 阶段存 JSON 数组，后续换 pgvector
    embedding: Mapped[list | None] = mapped_column(
        JSON, nullable=True, comment="向量嵌入（list[float]）"
    )

    # 知识点标签：必须挂载到 kp_taxonomy.json 的节点上
    kp_tags: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, comment="知识点ID列表（JSON数组）"
    )

    # 原始来源 URL（公开资料可追溯）
    source_url: Mapped[str] = mapped_column(
        String(512), nullable=False, default="", comment="原始来源URL"
    )

    # 切片版本号：每次重新切片后递增
    version: Mapped[str] = mapped_column(
        String(32), nullable=False, default="v0.1", comment="切片版本号"
    )

    # 在原始文档中的顺序（用于连续上下文检索）
    seq_index: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="文档内顺序号"
    )

    def to_dict(self) -> dict:
        return {
            "chunkId": self.chunk_id,
            "docId": self.doc_id,
            "content": self.content,
            "embedding": self.embedding or [],
            "kpTags": self.kp_tags or [],
            "sourceUrl": self.source_url,
            "version": self.version,
            "seqIndex": self.seq_index,
        }
