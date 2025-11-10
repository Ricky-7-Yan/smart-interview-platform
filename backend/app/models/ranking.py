"""
头衔权益模型：定义头衔和权益相关的数据库表结构
"""
from sqlalchemy import Column, Integer, String, TIMESTAMP, Index
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.sql import func
from app.database.connection import Base


class TitleBenefit(Base):
    """头衔权益表模型"""
    __tablename__ = "title_benefits"

    id = Column(Integer, primary_key=True, index=True)
    title_name = Column(String(50), unique=True, nullable=False)
    min_level = Column(Integer, nullable=False, index=True)
    max_level = Column(Integer, index=True)
    benefits = Column(JSON, nullable=False)  # 权益JSON {"unlocked_features": [...], "description": "..."}
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<TitleBenefit(title={self.title_name}, level={self.min_level}-{self.max_level})>"