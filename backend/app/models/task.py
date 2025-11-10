"""
任务模型：定义任务相关的数据库表结构
"""
from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey, TIMESTAMP, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base
import enum

class TaskType(enum.Enum):
    """任务类型枚举"""
    CUSTOM = "custom"
    REMEDIAL = "remedial"
    POSITION_BASED = "position_based"  # 确保值与数据库中的字符串匹配

class TaskStatus(enum.Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"

class Task(Base):
    """任务表模型"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    task_type = Column(Enum(TaskType, values_callable=lambda x: [e.value for e in x]), nullable=False)  # 修复：使用values_callable
    title = Column(String(200), nullable=False)
    description = Column(Text)
    position_category = Column(String(100), index=True)
    difficulty_level = Column(Integer, default=1)
    experience_reward = Column(Integer, default=10)
    status = Column(Enum(TaskStatus, values_callable=lambda x: [e.value for e in x]), default=TaskStatus.PENDING)  # 修复：使用values_callable
    related_interview_id = Column(Integer, ForeignKey("interviews.id"))
    created_at = Column(TIMESTAMP, server_default=func.now())
    completed_at = Column(TIMESTAMP, nullable=True)

    # 关系
    user = relationship("User", backref="tasks")

    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, status={self.status.value})>"