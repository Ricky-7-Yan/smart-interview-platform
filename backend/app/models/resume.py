"""
简历模型：存储用户上传的简历信息
"""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, JSON, Index
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base


class Resume(Base):
    """简历表"""
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 简历基本信息
    file_path = Column(String(500), nullable=True, comment='简历文件路径')
    file_name = Column(String(255), nullable=True, comment='文件名')
    file_type = Column(String(50), nullable=True, comment='文件类型: pdf, docx, txt等')

    # 解析后的结构化数据
    parsed_data = Column(JSON, nullable=True, comment='解析后的简历数据: name, education, experience, skills等')
    raw_text = Column(Text, nullable=True, comment='原始文本内容')

    # 元数据
    is_active = Column(Integer, default=1, comment='是否激活: 1-是, 0-否')
    version = Column(Integer, default=1, comment='版本号')

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", backref="resumes")

    def __repr__(self):
        return f"<Resume(id={self.id}, user_id={self.user_id}, file_name={self.file_name})>"