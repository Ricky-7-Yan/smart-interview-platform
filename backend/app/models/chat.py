"""
对话历史模型：存储用户与AI的对话记录
"""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, JSON, Index
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class ChatMessage(Base):
    """对话消息表"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True, comment='对话会话ID')
    role = Column(String(20), nullable=False, comment='角色: user, assistant, system')
    content = Column(Text, nullable=False, comment='消息内容')
    meta_data = Column(JSON, nullable=True, comment='元数据: 功能类型、推荐内容等')
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)

    user = relationship("User", backref="chat_messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role}, session_id={self.session_id})>"

class ChatSession(Base):
    """对话会话表"""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    context_type = Column(String(50), nullable=True, comment='上下文类型: learning, personalized, general')
    summary = Column(Text, nullable=True, comment='会话摘要')
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", backref="chat_sessions")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, session_id={self.session_id}, context_type={self.context_type})>"