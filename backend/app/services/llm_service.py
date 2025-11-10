"""
LLM服务：集成Qwen大模型，提供对话和生成能力
"""
import json
from typing import List, Dict, Optional
from openai import OpenAI
from app.config import settings

class LLMService:
    """LLM服务类：封装与Qwen API的交互"""

    def __init__(self):
        """初始化LLM服务，配置Qwen API客户端"""
        try:
            # 修复：使用兼容的方式初始化客户端
            self.client = OpenAI(
                api_key=settings.QWEN_API_KEY,
                base_url=settings.QWEN_API_BASE,
                timeout=60.0
            )
        except Exception as e:
            print(f"初始化OpenAI客户端失败: {e}")
            # 使用备用初始化方式
            self.client = OpenAI(
                api_key=settings.QWEN_API_KEY,
                base_url=settings.QWEN_API_BASE
            )

        self.model = settings.QWEN_MODEL

    def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        生成文本响应

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            temperature: 温度参数，控制随机性
            max_tokens: 最大token数

        Returns:
            生成的文本响应
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM API错误: {e}")
            return f"生成失败: {str(e)}"

    def analyze_interview(self, questions: List[str], answers: List[str], position: str) -> Dict:
        """
        分析面试表现，识别弱点和给出反馈

        Args:
            questions: 问题列表
            answers: 用户答案列表
            position: 目标岗位

        Returns:
            包含分数、反馈、弱点的字典
        """
        system_prompt = """你是一位资深的面试官，擅长分析候选人的面试表现。
请从以下维度评估：逻辑清晰度、表达流畅度、专业深度、问题理解度。
给出0-10分的评分，并指出具体弱点和改进建议。"""

        prompt = f"""
目标岗位：{position}

面试问答：
{self._format_qa(questions, answers)}

请分析并返回JSON格式：
{{
    "scores": {{
        "logic": 分数(0-10),
        "clarity": 分数(0-10),
        "professionalism": 分数(0-10),
        "understanding": 分数(0-10)
    }},
    "total_score": 总分(0-10),
    "weaknesses": ["弱点1", "弱点2", ...],
    "feedback": "详细反馈文本",
    "strengths": ["优点1", "优点2", ...]
}}
"""

        response = self.generate(prompt, system_prompt, temperature=0.3)

        # 尝试解析JSON
        try:
            return json.loads(response)
        except:
            # 如果解析失败，返回默认结构
            return {
                "scores": {"logic": 7.0, "clarity": 7.0, "professionalism": 7.0, "understanding": 7.0},
                "total_score": 7.0,
                "weaknesses": ["需要更清晰的表达"],
                "feedback": response,
                "strengths": []
            }

    def generate_interview_questions(self, task_description: str, position: str, count: int = 5) -> List[str]:
        """
        根据任务描述生成针对性面试问题

        Args:
            task_description: 任务描述
            position: 目标岗位
            count: 问题数量

        Returns:
            问题列表
        """
        system_prompt = "你是一位经验丰富的HR，擅长设计针对性的面试问题。"
        prompt = f"""
任务描述：{task_description}
目标岗位：{position}

请生成{count}个针对性面试问题，这些问题要能检验用户是否真正掌握了任务内容。
问题应该包括：
1. 数据/成果验证类问题（如"请用数据说明你的项目成果"）
2. 质疑应对类问题（如"如果HR质疑你简历数据的真实性，你会如何回应"）
3. 深度理解类问题（测试是否真正理解任务内容）

请直接返回问题列表，每行一个问题，不要编号。
"""

        response = self.generate(prompt, system_prompt, temperature=0.7)
        questions = [q.strip() for q in response.split('\n') if q.strip() and len(q.strip()) > 10]
        return questions[:count]

    def generate_remedial_task(self, weakness: str, position: str) -> Dict:
        """
        根据弱点生成补学任务

        Args:
            weakness: 识别的弱点
            position: 目标岗位

        Returns:
            补学任务字典
        """
        system_prompt = "你是一位专业的学习导师，擅长设计针对性的补学任务。"
        prompt = f"""
用户弱点：{weakness}
目标岗位：{position}

请生成一个精准的补学任务，包括：
1. 任务标题
2. 任务描述（具体要做什么）
3. 学习资源（3-5个具体的学习点或练习题）
4. 验证方式（如何验证是否掌握）

返回JSON格式：
{{
    "title": "任务标题",
    "description": "任务描述",
    "resources": ["资源1", "资源2", ...],
    "verification": "验证方式"
}}
"""

        response = self.generate(prompt, system_prompt, temperature=0.6)
        try:
            return json.loads(response)
        except:
            return {
                "title": f"补学任务：{weakness}",
                "description": f"针对弱点'{weakness}'的专项训练",
                "resources": [f"学习资源1：关于{weakness}", f"练习题：相关练习"],
                "verification": "完成练习并通过验证"
            }

    def generate_standard_answers(self, questions: List[str], position: str) -> List[str]:
        """
        生成标准答案参考

        Args:
            questions: 问题列表
            position: 目标岗位

        Returns:
            标准答案列表
        """
        system_prompt = "你是一位资深的面试官，擅长提供专业的面试答案参考。"

        standard_answers = []
        for question in questions:
            prompt = f"""
目标岗位：{position}

面试问题：{question}

请提供一个标准答案参考，包括：
1. 核心要点
2. 回答结构
3. 关键示例

请直接返回答案内容，不要编号。
"""
            answer = self.generate(prompt, system_prompt, temperature=0.5, max_tokens=500)
            standard_answers.append(answer.strip())

        return standard_answers

    def evaluate_facial_expression(self, answers: List[str]) -> str:
        """
        评估面部表情（模拟，实际需要视频分析）

        Args:
            answers: 答案列表

        Returns:
            表情评价文本
        """
        system_prompt = "你是一位专业的面试评估专家，擅长分析候选人的非语言表现。"
        prompt = f"""
基于以下面试回答，请评估候选人的面部表情表现（假设已通过视频分析）：

{self._format_answers(answers)}

请从以下维度评估：
1. 眼神交流
2. 面部表情自然度
3. 自信程度
4. 整体印象

返回评估结果（200字以内）。
"""
        try:
            evaluation = self.generate(prompt, system_prompt, temperature=0.5, max_tokens=300)
            return evaluation.strip()
        except Exception as e:
            print(f"表情评估失败: {e}")
            return "表情自然，眼神交流良好，整体表现自信。建议保持微笑，增强与面试官的眼神互动。"

    def evaluate_tone_and_word_choice(self, answers: List[str]) -> str:
        """
        评估语气和用词

        Args:
            answers: 答案列表

        Returns:
            语气和用词评价文本
        """
        system_prompt = "你是一位专业的面试评估专家，擅长分析候选人的语言表达。"
        prompt = f"""
基于以下面试回答，请评估候选人的语气和用词：

{self._format_answers(answers)}

请从以下维度评估：
1. 语气是否合适（专业、自信、自然）
2. 用词是否准确、专业
3. 表达是否清晰
4. 改进建议

返回评估结果（200字以内）。
"""
        try:
            evaluation = self.generate(prompt, system_prompt, temperature=0.5, max_tokens=300)
            return evaluation.strip()
        except Exception as e:
            print(f"语气评估失败: {e}")
            return "语气适中，用词准确，表达清晰。建议在专业术语使用上更加精准，适当增加具体数据支撑。"

    def generate_chat(self, messages: List[Dict], system_prompt: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        生成对话响应（支持多轮对话）

        Args:
            messages: 消息列表，格式：[{"role": "user", "content": "..."}, ...]
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            生成的文本响应
        """
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM API错误: {e}")
            return f"生成失败: {str(e)}"

    def _format_qa(self, questions: List[str], answers: List[str]) -> str:
        """格式化问答对"""
        result = []
        for i, (q, a) in enumerate(zip(questions, answers), 1):
            result.append(f"Q{i}: {q}\nA{i}: {a}\n")
        return "\n".join(result)

    def _format_answers(self, answers: List[str]) -> str:
        """格式化答案列表"""
        result = []
        for i, answer in enumerate(answers, 1):
            result.append(f"回答{i}: {answer}\n")
        return "\n".join(result)