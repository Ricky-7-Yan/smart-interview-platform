"""
任务笔记模型
"""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class TaskNote(Base):
    """任务笔记表"""
    __tablename__ = "task_notes"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False, comment='笔记内容')
    selected_text = Column(Text, nullable=True, comment='选中的文本')
    created_at = Column(TIMESTAMP, server_default=func.now())

    task = relationship("Task", backref="notes")
    user = relationship("User", backref="task_notes")

    def __repr__(self):
        return f"<TaskNote(id={self.id}, task_id={self.task_id})>"