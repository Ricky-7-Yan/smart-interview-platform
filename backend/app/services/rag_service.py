"""
RAG服务：实现检索增强生成，结合知识库回答问题
"""
import json
import numpy as np
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.services.llm_service import LLMService
from app.models.knowledge_base import KnowledgeBase

class RAGService:
    """RAG服务类：实现知识检索和增强生成"""

    def __init__(self):
        """初始化RAG服务，延迟加载embedding模型"""
        self.llm_service = LLMService()
        self.vector_dim = settings.VECTOR_DIMENSION
        self.top_k = settings.TOP_K_RETRIEVAL
        self._embedding_model = None  # 延迟加载

    @property
    def embedding_model(self):
        """延迟加载embedding模型"""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                # 尝试使用中文模型，如果失败则使用备用模型
                try:
                    # 使用国内镜像
                    import os
                    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
                    self._embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
                except Exception as e:
                    print(f"加载 {settings.EMBEDDING_MODEL} 失败: {e}")
                    print("使用备用embedding模型...")
                    # 使用轻量级备用模型
                    try:
                        self._embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                    except:
                        # 如果还是失败，使用更简单的模型
                        self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                        print("使用基础embedding模型")
            except Exception as e:
                print(f"初始化embedding模型失败: {e}")
                print("RAG功能将使用简化模式（仅文本检索）")
                self._embedding_model = None

        return self._embedding_model

    def get_embedding(self, text: str) -> List[float]:
        """
        获取文本的embedding向量

        Args:
            text: 输入文本

        Returns:
            embedding向量列表
        """
        if self.embedding_model is None:
            # 如果模型未加载，返回空向量（简化模式）
            return [0.0] * self.vector_dim

        try:
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            print(f"生成embedding失败: {e}")
            return [0.0] * self.vector_dim

    def search_knowledge(self, query: str, position_category: Optional[str] = None, db: Optional[Session] = None, top_k: int = None) -> List[Dict]:
        """
        在知识库中搜索相关文档

        Args:
            query: 查询文本
            position_category: 岗位类别（可选）
            db: 数据库会话
            top_k: 返回数量

        Returns:
            相关文档列表
        """
        if top_k is None:
            top_k = self.top_k

        if db is None:
            return []

        try:
            # 简化版本：直接文本搜索（实际应该使用向量相似度）
            if position_category:
                docs = db.query(KnowledgeBase).filter(
                    KnowledgeBase.position_category == position_category
                ).limit(top_k).all()
            else:
                docs = db.query(KnowledgeBase).limit(top_k).all()

            result = []
            for doc in docs:
                result.append({
                    "id": doc.id,
                    "title": doc.title,
                    "content": doc.content[:500],  # 截取前500字符
                    "category": doc.category,
                    "position_category": doc.position_category
                })

            return result
        except Exception as e:
            print(f"搜索知识库失败: {e}")
            return []

    def generate_answer_with_context(self, question: str, position_category: str, db: Session) -> str:
        """
        基于检索到的知识生成答案

        Args:
            question: 问题
            position_category: 岗位类别
            db: 数据库会话

        Returns:
            生成的答案
        """
        # 检索相关知识
        context_docs = self.search_knowledge(question, position_category, db)

        # 构建上下文
        context = "\n".join([f"{doc['title']}: {doc['content']}" for doc in context_docs])

        system_prompt = f"你是一位专业的面试导师，擅长回答{position_category}相关的面试问题。"
        prompt = f"""
基于以下知识库内容回答问题：

{context if context else '暂无相关知识库内容，请根据你的专业知识回答。'}

问题：{question}

请结合知识库内容，给出专业、准确的回答。
"""

        return self.llm_service.generate(prompt, system_prompt, temperature=0.5)