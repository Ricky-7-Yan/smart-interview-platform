"""
配置文件：管理所有应用配置，包括数据库、API密钥等
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "123456"
    DB_NAME: str = "smart_interview"

    # Qwen API配置
    QWEN_API_KEY: str = "sk-484fb339d2274307b3aa3fd6400964ae"
    QWEN_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_MODEL: str = "qwen-plus"  # 可选: qwen-plus, qwen-turbo, qwen-max

    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # RAG配置
    EMBEDDING_MODEL: str = "text2vec-base-chinese"  # 使用中文embedding模型
    VECTOR_DIMENSION: int = 768
    TOP_K_RETRIEVAL: int = 5

    # 训练配置
    MODEL_PATH: str = "./models"
    TRAINING_DATA_PATH: str = "./data/training"
    BATCH_SIZE: int = 8
    LEARNING_RATE: float = 2e-5
    EPOCHS: int = 3

    # 前端配置
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()