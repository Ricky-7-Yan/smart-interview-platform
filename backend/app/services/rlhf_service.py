"""
RLHF服务：实现强化学习人类反馈优化
"""
import json
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.services.llm_service import LLMService


class RLHFService:
    """RLHF服务：实现SFT和RLHF训练流程"""

    def __init__(self):
        """初始化RLHF服务"""
        self.llm_service = LLMService()

    def collect_preference_data(self, prompt: str, response_a: str, response_b: str,
                                preference: int, position_category: str, db: Session):
        """
        收集偏好数据用于RLHF训练

        Args:
            prompt: 提示词
            response_a: 响应A
            response_b: 响应B
            preference: 偏好（1表示A更好，-1表示B更好，0表示同等）
            position_category: 岗位类别
            db: 数据库会话
        """
        sql = """
        INSERT INTO training_data (prompt, response, reference_response, preference_score, position_category)
        VALUES (:prompt, :response, :reference, :score, :position)
        """

        preferred_response = response_a if preference > 0 else response_b
        reference_response = response_b if preference > 0 else response_a
        score = abs(preference) * 0.5 + 0.5  # 转换为0-1分数

        db.execute(sql, {
            "prompt": prompt,
            "response": preferred_response,
            "reference": reference_response,
            "score": score,
            "position": position_category
        })
        db.commit()

    def generate_training_data(self, position_category: str, db: Session, count: int = 100):
        """
        生成训练数据

        Args:
            position_category: 岗位类别
            count: 生成数量
            db: 数据库会话
        """
        # 这里可以从真实面试数据中生成训练样本
        prompts = [
            f"请介绍一下你在{position_category}方面的项目经验",
            f"如果遇到{position_category}相关的问题，你会如何处理？",
            f"请用数据说明你在{position_category}项目中的成果"
        ]

        for _ in range(count):
            prompt = prompts[_ % len(prompts)]
            # 使用LLM生成多个响应
            response_a = self.llm_service.generate(f"{prompt}\n请给出一个较差的回答。", temperature=0.9)
            response_b = self.llm_service.generate(f"{prompt}\n请给出一个优秀的回答。", temperature=0.7)

            # 自动标注偏好（实际应该由人工标注）
            preference = 1  # 假设response_b更好

            self.collect_preference_data(prompt, response_a, response_b, preference, position_category, db)