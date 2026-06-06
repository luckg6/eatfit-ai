from sqlalchemy import Column, BigInteger, String, DateTime, Text, Integer, ForeignKey, DECIMAL, JSON, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class MemoryItem(Base):
    __tablename__ = "memory_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    memory_type = Column(String(64), nullable=False)
    content = Column(Text, nullable=False)
    importance_score = Column(Integer, nullable=False, default=5)
    status = Column(String(32), nullable=False, default="active")  # active, inactive, superseded, pending
    confidence_score = Column(DECIMAL(4, 2), default=0.80)
    source = Column(String(64), nullable=False, default="manual")
    source_message_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    last_used_at = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    # embedding 是 pgvector 列；ORM 不直接持有此列，通过 MemoryTools 走 raw SQL 读写
    # 这里保留字段名以供业务代码引用
    embedding_status = Column(String(32), nullable=False, default="pending")
    embedding_updated_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="memories")