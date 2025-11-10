"""
Benchmark评估：评估模型性能
"""
import json
from typing import List, Dict
from app.services.llm_service import LLMService
from app.training.sft_trainer import SFTTrainer
from app.training.rlhf_trainer import RLHFTrainer


class BenchmarkEvaluator:
    """Benchmark评估器"""

    def __init__(self):
        """初始化评估器"""
        self.llm_service = LLMService()
        self.metrics = {
            "accuracy": 0.0,
            "relevance": 0.0,
            "coherence": 0.0,
            "helpfulness": 0.0
        }

    def evaluate_model(self, model_type: str, test_data: List[Dict]) -> Dict:
        """
        评估模型性能

        Args:
            model_type: 模型类型 ("base", "sft", "rlhf")
            test_data: 测试数据 [{"prompt": "...", "expected": "..."}, ...]

        Returns:
            评估结果字典
        """
        results = {
            "total": len(test_data),
            "correct": 0,
            "accuracy": 0.0,
            "avg_relevance": 0.0,
            "avg_coherence": 0.0
        }

        for item in test_data:
            prompt = item["prompt"]
            expected = item.get("expected", "")

            # 生成回答
            if model_type == "base":
                response = self.llm_service.generate(prompt)
            elif model_type == "sft":
                # 使用SFT模型
                trainer = SFTTrainer()
                trainer.load_model()
                response = trainer.generate(prompt)
            elif model_type == "rlhf":
                # 使用RLHF模型
                trainer = RLHFTrainer()
                trainer.load_model()
                response = trainer.generate(prompt)
            else:
                response = self.llm_service.generate(prompt)

            # 评估相关性（使用LLM评估）
            relevance_score = self._evaluate_relevance(prompt, response, expected)
            results["avg_relevance"] += relevance_score

            # 评估连贯性
            coherence_score = self._evaluate_coherence(response)
            results["avg_coherence"] += coherence_score

        # 计算平均分
        results["avg_relevance"] /= len(test_data)
        results["avg_coherence"] /= len(test_data)
        results["accuracy"] = results["correct"] / results["total"] if results["total"] > 0 else 0

        return results

    def _evaluate_relevance(self, prompt: str, response: str, expected: str) -> float:
        """评估相关性"""
        evaluation_prompt = f"""
请评估以下回答与问题的相关性（0-10分）：

问题：{prompt}
回答：{response}
期望：{expected}

请只返回一个0-10之间的数字分数。
"""
        score_text = self.llm_service.generate(evaluation_prompt, temperature=0.1)
        try:
            return float(score_text.strip())
        except:
            return 7.0

    def _evaluate_coherence(self, response: str) -> float:
        """评估连贯性"""
        evaluation_prompt = f"""
请评估以下回答的连贯性（0-10分）：

回答：{response}

请只返回一个0-10之间的数字分数。
"""
        score_text = self.llm_service.generate(evaluation_prompt, temperature=0.1)
        try:
            return float(score_text.strip())
        except:
            return 7.0

    def compare_models(self, test_data: List[Dict]) -> Dict:
        """
        对比不同模型的性能

        Args:
            test_data: 测试数据

        Returns:
            对比结果
        """
        results = {}

        for model_type in ["base", "sft", "rlhf"]:
            print(f"评估 {model_type} 模型...")
            results[model_type] = self.evaluate_model(model_type, test_data)

        return results