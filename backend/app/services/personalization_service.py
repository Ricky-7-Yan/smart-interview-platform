"""
个性化服务：根据用户数据提供个性化推荐和优化
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.services.llm_service import LLMService
from app.models.user_preference import UserPreference
from app.models.interview import Interview
from app.models.task import Task


class PersonalizationService:
    """个性化服务类"""

    def __init__(self):
        self.llm_service = LLMService()

    def analyze_user_style(self, user_id: int, db: Session) -> Dict:
        """分析用户的沟通风格和学习习惯"""
        # 获取用户最近的对话和回答
        from app.models.chat import ChatMessage

        recent_messages = db.query(ChatMessage).filter(
            ChatMessage.user_id == user_id,
            ChatMessage.role == "user"
        ).order_by(ChatMessage.created_at.desc()).limit(20).all()

        if not recent_messages:
            return {}

        # 分析语气和措辞
        sample_texts = [msg.content for msg in recent_messages[:10]]
        combined_text = "\n".join(sample_texts)

        prompt = f"""
分析以下用户文本的语气和措辞特点：

{combined_text}

请返回JSON格式：
{{
    "tone": "语气特点（formal/casual/friendly/professional）",
    "formality": "正式程度（1-5）",
    "verbosity": "详细程度（concise/moderate/detailed）",
    "key_phrases": ["用户常用的短语或表达方式"]
}}
"""

        system_prompt = "你是一位专业的文本分析专家，擅长分析语言风格。"
        result = self.llm_service.generate(prompt, system_prompt, temperature=0.3)

        try:
            import json
            return json.loads(result)
        except:
            return {
                "tone": "friendly",
                "formality": 3,
                "verbosity": "moderate",
                "key_phrases": []
            }

    def adapt_ai_tone(self, user_style: Dict, base_tone: str = "friendly") -> str:
        """根据用户风格调整AI语气"""
        user_tone = user_style.get("tone", "friendly")
        formality = user_style.get("formality", 3)

        # 匹配用户语气
        if user_tone == "formal" or formality >= 4:
            return "professional"
        elif user_tone == "casual" or formality <= 2:
            return "casual"
        else:
            return base_tone

    def generate_personalized_questions(
            self,
            resume_data: Dict,
            user_preference: Optional[UserPreference],
            count: int = 5
    ) -> List[str]:
        """基于简历生成个性化问题"""
        system_prompt = """你是一位经验丰富的HR，擅长根据简历设计针对性面试问题。"""

        weak_areas = []
        if user_preference and user_preference.weak_areas:
            weak_areas = [w["area"] for w in user_preference.weak_areas[:3]]

        prompt = f"""
基于以下简历信息生成{count}个针对性面试问题：

简历信息：
{self._format_resume_data(resume_data)}

用户薄弱领域：{', '.join(weak_areas) if weak_areas else '无'}

要求：
1. 问题要能验证简历内容的真实性
2. 针对薄弱领域设计挑战性问题
3. 包含行为面试、技术面试、情景面试等类型
4. 问题要有一定难度，能真正测试能力

请直接返回问题列表，每行一个问题，不要编号。
"""

        response = self.llm_service.generate(prompt, system_prompt, temperature=0.7)
        questions = [q.strip() for q in response.split('\n') if q.strip() and len(q.strip()) > 10]
        return questions[:count]

    def recommend_learning_path(self, user_id: int, db: Session) -> Dict:
        """推荐个性化学习路径"""
        preference = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()

        if not preference or not preference.weak_areas:
            return {
                "recommended_tasks": [],
                "focus_areas": [],
                "learning_plan": "建议先完成基础学习任务，建立知识体系。"
            }

        # 根据薄弱领域推荐任务
        weak_areas = sorted(preference.weak_areas, key=lambda x: x.get("score", 0))[:3]

        focus_areas = [w["area"] for w in weak_areas]

        learning_plan = f"""
基于你的学习表现，建议重点关注以下领域：
{', '.join(focus_areas)}

学习建议：
1. 优先完成{focus_areas[0]}相关的学习任务
2. 多进行模拟面试练习
3. 针对薄弱点进行专项训练
"""

        return {
            "recommended_tasks": focus_areas,
            "focus_areas": focus_areas,
            "learning_plan": learning_plan
        }

    def _format_resume_data(self, resume_data: Dict) -> str:
        """格式化简历数据"""
        result = []
        if resume_data.get("name"):
            result.append(f"姓名：{resume_data['name']}")
        if resume_data.get("education"):
            result.append(f"教育背景：{resume_data['education']}")
        if resume_data.get("experience"):
            result.append(f"工作经历：{resume_data['experience']}")
        if resume_data.get("skills"):
            result.append(
                f"技能：{', '.join(resume_data['skills']) if isinstance(resume_data['skills'], list) else resume_data['skills']}")
        return "\n".join(result)