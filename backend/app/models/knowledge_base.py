"""
知识库模型：存储RAG知识库数据
"""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Index
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.sql import func
from app.database.connection import Base


class KnowledgeBase(Base):
    """知识库表模型"""
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), index=True)
    position_category = Column(String(100), index=True)
    embedding_vector = Column(JSON)  # 存储向量
    meta_data = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, title={self.title[:50]})>"