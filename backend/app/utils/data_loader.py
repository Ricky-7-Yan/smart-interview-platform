"""
数据加载工具：从外部数据源加载训练数据和知识库数据
"""
import json
import os
import requests
from typing import List, Dict
from sqlalchemy.orm import Session
from app.models.interview import Interview
from app.models.knowledge_base import KnowledgeBase


class DataLoader:
    """数据加载器：加载公开数据集和知识库内容"""

    @staticmethod
    def load_interview_dataset(position_category: str) -> List[Dict]:
        """
        加载面试数据集（从公开数据集或生成）

        这里可以从以下来源获取数据：
        1. GitHub公开数据集
        2. 爬取公开面试网站
        3. 使用LLM生成高质量数据
        """
        # 示例：可以从这些来源获取数据
        sources = [
            "https://github.com/topics/interview-questions",
            "https://github.com/topics/chinese-interview",
        ]

        # 这里返回模拟数据，实际应该从真实数据源加载
        dataset = [
            {
                "question": f"请介绍一下你在{position_category}方面的项目经验",
                "reference_answer": f"我在{position_category}领域有3年经验，曾主导过多个项目...",
                "category": position_category,
                "difficulty": 3
            }
        ]

        return dataset

    @staticmethod
    def load_knowledge_base_data(position_category: str) -> List[Dict]:
        """
        加载知识库数据

        可以从以下来源获取：
        1. 技术文档
        2. 面试指南
        3. 行业报告
        """
        knowledge_items = [
            {
                "title": f"{position_category}核心技能要求",
                "content": f"{position_category}需要掌握的核心技能包括...",
                "category": "技能要求",
                "position_category": position_category
            },
            {
                "title": f"{position_category}常见面试问题",
                "content": f"{position_category}面试中常见的问题类型包括...",
                "category": "面试问题",
                "position_category": position_category
            }
        ]

        return knowledge_items

    @staticmethod
    def populate_knowledge_base(db: Session, position_categories: List[str]):
        """
        填充知识库

        Args:
            db: 数据库会话
            position_categories: 岗位类别列表
        """
        from app.services.rag_service import RAGService
        rag = RAGService()

        for category in position_categories:
            items = DataLoader.load_knowledge_base_data(category)
            for item in items:
                # 生成embedding
                embedding = rag.get_embedding(item["content"])

                kb_item = KnowledgeBase(
                    title=item["title"],
                    content=item["content"],
                    category=item["category"],
                    position_category=item["position_category"],
                    embedding_vector=json.dumps(embedding)
                )
                db.add(kb_item)

        db.commit()