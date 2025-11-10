"""
用户模型：定义用户数据库表结构
"""
from sqlalchemy import Column, Integer, String, TIMESTAMP, Index
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.sql import func
from app.database.connection import Base

class User(Base):
    """用户表模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # 新字段：支持多个岗位
    target_positions = Column(JSON, nullable=True, comment='目标岗位列表(JSON数组)')

    # 保留旧字段用于兼容（如果数据库还有这个字段）
    # 注意：如果数据库已经删除了 target_position，这行会报错，需要注释掉
    # target_position = Column(String(100), nullable=True)

    current_level = Column(Integer, default=1)
    experience_points = Column(Integer, default=0)
    title = Column(String(50), default="新手")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, level={self.current_level})>"

    @property
    def get_target_positions(self):
        """获取目标岗位列表（兼容新旧字段）"""
        if self.target_positions is not None:
            if isinstance(self.target_positions, list):
                return self.target_positions
            else:
                return [self.target_positions] if self.target_positions else []
        # 如果没有新字段，尝试从旧字段读取（向后兼容）
        # if hasattr(self, 'target_position') and self.target_position:
        #     return [self.target_position]
        return []