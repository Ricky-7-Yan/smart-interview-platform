"""
用户偏好模型：存储用户的学习习惯和偏好
"""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, JSON, Numeric, Index
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base


class UserPreference(Base):
    """用户偏好表"""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    # 学习偏好
    preferred_learning_style = Column(String(50), nullable=True,
                                      comment='学习风格: visual, auditory, reading, kinesthetic')
    preferred_difficulty = Column(String(20), default='medium', comment='偏好难度: easy, medium, hard')
    preferred_question_types = Column(JSON, nullable=True, comment='偏好的问题类型列表')

    # 沟通风格偏好
    communication_style = Column(JSON, nullable=True, comment='沟通风格: tone, formality, verbosity等')
    ai_tone_preference = Column(String(50), default='friendly',
                                comment='AI语气偏好: friendly, professional, casual, formal')

    # 学习数据统计
    weak_areas = Column(JSON, nullable=True, comment='薄弱领域: [{"area": "算法", "score": 5.2, "count": 10}]')
    strong_areas = Column(JSON, nullable=True, comment='强项领域')
    learning_history = Column(JSON, nullable=True, comment='学习历史统计')

    # 个性化设置
    custom_instructions = Column(Text, nullable=True, comment='用户自定义指令')
    feedback_preferences = Column(JSON, nullable=True, comment='反馈偏好设置')

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", backref="preference", uselist=False)

    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id}, style={self.preferred_learning_style})>"


class UserFeedback(Base):
    """用户反馈表"""
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    feedback_type = Column(String(50), nullable=False, comment='反馈类型: interview, chat, recommendation等')
    content = Column(Text, nullable=False, comment='反馈内容')
    rating = Column(Integer, nullable=True, comment='评分1-5')
    meta_data = Column(JSON, nullable=True, comment='相关元数据')
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)

    user = relationship("User", backref="feedbacks")

    def __repr__(self):
        return f"<UserFeedback(id={self.id}, type={self.feedback_type}, rating={self.rating})>"