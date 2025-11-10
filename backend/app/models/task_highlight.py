"""
任务标注模型
"""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class TaskHighlight(Base):
    """任务标注表"""
    __tablename__ = "task_highlights"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, nullable=False, comment='标注的文本')
    created_at = Column(TIMESTAMP, server_default=func.now())

    task = relationship("Task", backref="highlights")
    user = relationship("User", backref="task_highlights")

    def __repr__(self):
        return f"<TaskHighlight(id={self.id}, task_id={self.task_id})>"