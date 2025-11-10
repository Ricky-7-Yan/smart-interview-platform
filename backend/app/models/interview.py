"""
面试模型：定义面试相关的数据库表结构
"""
from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey, TIMESTAMP, Numeric, Index
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base
import enum

class InterviewType(enum.Enum):
    """面试类型枚举"""
    TASK_BASED = "task_based"
    STAGE_BASED = "stage_based"
    REMEDIAL = "remedial"

class InterviewStatus(enum.Enum):
    """面试状态枚举"""
    PENDING = "pending"
    COMPLETED = "completed"
    REVIEWED = "reviewed"

class Interview(Base):
    """面试表模型"""
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    interview_type = Column(Enum(InterviewType, values_callable=lambda x: [e.value for e in x]), nullable=False)  # 修复
    related_task_id = Column(Integer, ForeignKey("tasks.id"), index=True)
    stage_number = Column(Integer)
    questions = Column(JSON)
    answers = Column(JSON)
    ai_feedback = Column(JSON)
    scores = Column(JSON)
    weaknesses = Column(JSON)
    total_score = Column(Numeric(5, 2))
    status = Column(Enum(InterviewStatus, values_callable=lambda x: [e.value for e in x]), default=InterviewStatus.PENDING)  # 修复
    created_at = Column(TIMESTAMP, server_default=func.now())
    completed_at = Column(TIMESTAMP, nullable=True)

    # 关系
    user = relationship("User", backref="interviews")

    def __repr__(self):
        return f"<Interview(id={self.id}, type={self.interview_type.value}, score={self.total_score})>"