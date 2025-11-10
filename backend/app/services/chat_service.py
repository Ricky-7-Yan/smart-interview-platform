"""
对话服务：处理AI对话逻辑，包括功能介绍、推荐、反馈收集等
"""
import json
import uuid
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from app.services.llm_service import LLMService
from app.models.chat import ChatMessage, ChatSession
from app.models.user_preference import UserPreference, UserFeedback
from app.models.user import User
from app.models.interview import Interview
from app.models.task import Task


class ChatService:
    """对话服务类：处理智能对话逻辑"""

    def __init__(self):
        self.llm_service = LLMService()

    def get_or_create_session(self, user_id: int, context_type: str = "general", db: Session = None) -> str:
        """获取或创建对话会话"""
        session_id = f"session_{user_id}_{uuid.uuid4().hex[:8]}"

        # 查找最近的活跃会话
        existing_session = db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.context_type == context_type
        ).order_by(ChatSession.updated_at.desc()).first()

        if existing_session:
            # 检查会话是否过期（24小时）
            from datetime import datetime, timedelta
            if datetime.now() - existing_session.updated_at < timedelta(hours=24):
                return existing_session.session_id

        # 创建新会话
        new_session = ChatSession(
            user_id=user_id,
            session_id=session_id,
            context_type=context_type
        )
        db.add(new_session)
        db.commit()
        return session_id

    def get_conversation_history(self, session_id: str, limit: int = 20, db: Session = None) -> List[Dict]:
        """获取对话历史"""
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).limit(limit).all()

        return [
            {
                "role": msg.role,
                "content": msg.content,
                "metadata": msg.meta_data or {},
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ]

    def get_user_context(self, user: User, db: Session) -> Dict:
        """获取用户上下文信息"""
        # 获取用户偏好
        preference = db.query(UserPreference).filter(UserPreference.user_id == user.id).first()

        # 获取最近的学习数据
        recent_interviews = db.query(Interview).filter(
            Interview.user_id == user.id,
            Interview.status == "completed"
        ).order_by(Interview.created_at.desc()).limit(5).all()

        recent_tasks = db.query(Task).filter(
            Task.user_id == user.id
        ).order_by(Task.created_at.desc()).limit(5).all()

        # 分析薄弱领域
        weak_areas = []
        if preference and preference.weak_areas:
            weak_areas = preference.weak_areas

        # 分析强项
        strong_areas = []
        if preference and preference.strong_areas:
            strong_areas = preference.strong_areas

        return {
            "user_info": {
                "username": user.username,
                "level": user.current_level,
                "title": user.title,
                "target_positions": user.target_positions or []
            },
            "preference": {
                "learning_style": preference.preferred_learning_style if preference else None,
                "ai_tone": preference.ai_tone_preference if preference else "friendly",
                "communication_style": preference.communication_style if preference else {}
            },
            "recent_activity": {
                "interviews_count": len(recent_interviews),
                "tasks_count": len(recent_tasks),
                "avg_score": sum([i.total_score or 0 for i in recent_interviews]) / len(
                    recent_interviews) if recent_interviews else 0
            },
            "weak_areas": weak_areas,
            "strong_areas": strong_areas
        }

    def generate_greeting(self, user: User, db: Session, context_type: str = "general") -> str:
        """生成欢迎消息和功能介绍"""
        try:
            context = self.get_user_context(user, db)
            system_prompt = self._build_system_prompt(context, context_type)

            if context_type == "general":
                prompt = f"""请生成一条欢迎消息，包括：
1. 简短友好的问候
2. 平台核心功能简介（学习模块和个性化模块）
3. 询问用户今天想做什么

要求：
- 语气：轻松友好，像朋友聊天
- 长度：100-150字
- 只返回一条完整的消息，不要分段
"""
            elif context_type == "learning":
                prompt = f"""请生成一条学习模块的欢迎消息，包括：
1. 欢迎进入学习模块
2. 说明学习模块的功能（学习任务、知识点、练习）
3. 询问用户想学习什么

要求：
- 语气：专业但友好，像老师
- 长度：100-150字
- 只返回一条完整的消息，不要分段
"""
            else:  # personalized
                # 检查是否有简历
                from app.models.resume import Resume
                resume = db.query(Resume).filter(
                    Resume.user_id == user.id,
                    Resume.is_active == 1
                ).first()

                if resume:
                    prompt = f"""请生成一条个性化模块的欢迎消息，包括：
1. 欢迎回来，已检测到用户已上传简历
2. 说明可以基于简历进行个性化面试训练
3. 询问用户是否想开始面试训练

要求：
- 语气：贴心专业，像职业顾问
- 长度：100-150字
- 只返回一条完整的消息，不要分段
- 不要重复之前的欢迎消息
"""
                else:
                    prompt = f"""请生成一条个性化模块的欢迎消息，包括：
1. 欢迎进入个性化模块
2. 说明个性化功能（简历分析、针对性问题）
3. 询问是否需要上传简历

要求：
- 语气：贴心专业，像职业顾问
- 长度：100-150字
- 只返回一条完整的消息，不要分段
"""

            response = self.llm_service.generate(prompt, system_prompt, temperature=0.7, max_tokens=300)

            # 确保只返回一条消息，如果有多段，只取第一段
            if '\n\n' in response:
                paragraphs = response.split('\n\n')
                response = paragraphs[0].strip()

            return response
        except Exception as e:
            print(f"生成欢迎消息失败: {e}")
            # 返回默认欢迎消息 - 使用单引号避免引号冲突
            default_greetings = {
                "general": '你好！我是你的AI助手"小面"，有什么可以帮你的吗？',
                "learning": '欢迎进入学习模块！我是你的学习导师"学小面"。在这里，我会为你系统地讲解核心知识点，布置有针对性的学习任务，并提供练习题来巩固掌握程度。你现在想学习哪个方向的内容呢？',
                "personalized": '欢迎进入个性化模块！我是你的个性化面试顾问"个小面"。在这里，我会基于你的简历提供个性化的面试建议和针对性问题。请先上传你的简历，让我为你定制专属的面试训练方案。'
            }
            return default_greetings.get(context_type, default_greetings["general"])

    def process_user_message(
            self,
            user_id: int,
            message: str,
            session_id: str,
            context_type: str,
            db: Session
    ) -> Tuple[str, Dict]:
        """处理用户消息并生成回复"""
        try:
            # 获取对话历史
            history = self.get_conversation_history(session_id, limit=10, db=db)

            # 获取用户上下文
            user = db.query(User).filter(User.id == user_id).first()
            context = self.get_user_context(user, db)

            # 如果是个性化模块，获取简历信息
            resume_context = ""
            if context_type == "personalized":
                from app.models.resume import Resume
                resume = db.query(Resume).filter(
                    Resume.user_id == user_id,
                    Resume.is_active == 1
                ).first()
                if resume and resume.parsed_data:
                    resume_info = []
                    if resume.parsed_data.get('name'):
                        resume_info.append(f"姓名：{resume.parsed_data.get('name')}")
                    if resume.parsed_data.get('education'):
                        resume_info.append(f"教育背景：{resume.parsed_data.get('education')}")
                    if resume.parsed_data.get('experience'):
                        exp = resume.parsed_data.get('experience')
                        if isinstance(exp, list):
                            exp = ', '.join(exp[:3])  # 只取前3个
                        resume_info.append(f"工作经历：{exp}")
                    if resume.parsed_data.get('skills'):
                        skills = resume.parsed_data.get('skills')
                        if isinstance(skills, list):
                            skills = ', '.join(skills[:5])  # 只取前5个技能
                        resume_info.append(f"技能：{skills}")

                    if resume_info:
                        resume_context = f"""
用户简历信息：
{chr(10).join(resume_info)}
"""

            # 构建系统提示词
            system_prompt = self._build_system_prompt(context, context_type)
            if resume_context:
                system_prompt += resume_context

            # 构建对话历史
            messages = []
            for msg in history[-6:]:  # 只取最近6条
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            messages.append({"role": "user", "content": message})

            # 如果是个性化模块，添加特殊提示让对话更自然
            if context_type == "personalized":
                system_prompt += """
重要对话原则：
- 基于用户的简历内容，自然地提出面试问题
- 不要一次性问多个问题，一次只问一个问题
- 根据用户的回答，自然地引导到下一个相关问题
- 对话要流畅自然，像真实面试一样，不要生硬地列出"题目1"、"题目2"
- 在用户回答后，可以给出简短评价或反馈，然后自然地提出下一个问题
- 问题之间要有逻辑关联，根据用户回答的内容深入挖掘
- 如果用户回答得很好，可以适当肯定，然后引导到下一个相关话题
- 如果用户回答不够完整，可以追问细节，但不要过于生硬
- 整个对话应该像朋友间的职业咨询，而不是机械的问答
- 避免使用"接下来是第二题"、"现在问第三题"这样的表述
"""

            # 添加重要提示：只返回一条回复
            system_prompt += "\n\n重要：请只返回一条完整的回复，不要分段或多条消息。"

            # 生成回复
            response = self.llm_service.generate_chat(
                messages,
                system_prompt,
                temperature=0.7,
                max_tokens=1000  # 限制token数，确保回复不会太长
            )

            # 确保只返回一条消息
            if '\n\n' in response:
                paragraphs = response.split('\n\n')
                # 如果第一段太短，合并前两段
                if len(paragraphs[0]) < 50 and len(paragraphs) > 1:
                    response = paragraphs[0] + '\n\n' + paragraphs[1]
                else:
                    response = paragraphs[0]

            # 检测意图和推荐功能
            intent = self._detect_intent(message, context)
            recommendations = self._generate_recommendations(intent, context, db)

            # 保存消息
            self._save_message(user_id, session_id, "user", message, {}, db)
            self._save_message(
                user_id,
                session_id,
                "assistant",
                response,
                {"intent": intent, "recommendations": recommendations},
                db
            )

            return response, {
                "intent": intent,
                "recommendations": recommendations,
                "suggested_actions": self._get_suggested_actions(intent)
            }
        except Exception as e:
            print(f"处理用户消息失败: {e}")
            import traceback
            traceback.print_exc()
            # 返回友好的错误消息
            return "抱歉，我暂时无法处理这个问题，请稍后再试。", {
                "intent": "error",
                "recommendations": [],
                "suggested_actions": []
            }

    def collect_feedback(
            self,
            user_id: int,
            feedback_type: str,
            content: str,
            rating: Optional[int] = None,
            metadata: Optional[Dict] = None,
            db: Session = None
    ):
        """收集用户反馈并更新偏好"""
        # 保存反馈
        feedback = UserFeedback(
            user_id=user_id,
            feedback_type=feedback_type,
            content=content,
            rating=rating,
            meta_data=metadata or {}
        )
        db.add(feedback)

        # 更新用户偏好
        self._update_preferences_from_feedback(user_id, feedback_type, content, rating, metadata, db)

        db.commit()

    def update_learning_analytics(
            self,
            user_id: int,
            interview_id: int,
            db: Session
    ):
        """根据面试结果更新学习分析"""
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview or interview.status != "completed":
            return

        preference = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if not preference:
            preference = UserPreference(user_id=user_id)
            db.add(preference)

        # 分析弱点并更新
        weaknesses = interview.weaknesses or []
        scores = interview.scores or {}

        # 更新薄弱领域
        weak_areas = preference.weak_areas or []
        for weakness in weaknesses:
            # 查找或创建薄弱领域记录
            found = False
            for area in weak_areas:
                if area.get("area") == weakness:
                    area["count"] = area.get("count", 0) + 1
                    area["score"] = (area.get("score", 0) * (area["count"] - 1) + interview.total_score) / area["count"]
                    found = True
                    break
            if not found:
                weak_areas.append({
                    "area": weakness,
                    "score": float(interview.total_score or 0),
                    "count": 1
                })

        preference.weak_areas = weak_areas
        db.commit()

    def _build_system_prompt(self, context: Dict, context_type: str) -> str:
        """构建系统提示词"""
        base_info = f"""用户信息：
- 等级：{context['user_info']['level']} ({context['user_info']['title']})
- 目标岗位：{', '.join(context['user_info']['target_positions']) if context['user_info']['target_positions'] else '未设置'}
"""

        if context_type == "general":
            # 通用AI助手 - 友好、轻松、多功能的助手
            system_prompt = f"""你是"小面"，一位友好、幽默、多才多艺的AI面试学习助手。你的特点是：
1. **性格**：活泼开朗，像朋友一样亲切，偶尔会开小玩笑
2. **功能**：可以回答各种问题，推荐功能，帮助导航，提供学习建议
3. **语气**：轻松自然，像在和朋友聊天，不要太正式
4. **能力**：了解平台所有功能，能根据用户需求推荐合适的模块

{base_info}

重要原则：
- 用轻松、友好的语气交流
- 主动询问用户需求，提供建议
- 如果用户问的问题你不确定，可以引导他们到相应模块
- 保持积极正面的态度，鼓励用户学习
- 每次只回复一条消息，不要分段
"""

        elif context_type == "learning":
            # 学习模块AI - 专业、严谨、教学导向
            system_prompt = f"""你是"学小面"，一位专业、严谨的学习导师。你的特点是：
1. **性格**：专业认真，像一位经验丰富的老师
2. **功能**：专注于学习任务、知识点讲解、学习路径规划
3. **语气**：专业但不过于严肃，清晰有条理
4. **能力**：深入讲解知识点，设计学习计划，提供学习资源

{base_info}

用户薄弱领域：{', '.join([w['area'] for w in context['weak_areas'][:3]]) if context['weak_areas'] else '暂无'}

重要原则：
- 用专业但易懂的语言讲解知识点
- 根据薄弱领域推荐针对性学习内容
- 提供具体的学习建议和资源
- 鼓励用户完成学习任务，跟踪学习进度
- 可以生成学习任务、解释概念、提供练习题
- 每次只回复一条消息，不要分段
"""

        elif context_type == "personalized":
            # 个性化模块AI - 贴心、定制化、简历导向
            system_prompt = f"""你是"个小面"，一位贴心的个性化面试顾问。你的特点是：
1. **性格**：细心体贴，像一位专业的职业规划师
2. **功能**：基于用户简历提供个性化建议，生成针对性问题
3. **语气**：温和专业，像在给朋友提供职业建议
4. **能力**：分析简历，设计面试问题，优化面试表现

{base_info}

重要原则：
- 基于用户的简历内容提供建议
- 生成针对性的面试问题
- 提供面试技巧和优化建议
- 帮助用户准备面试，提升表现
- 语气要贴心，像在帮助朋友准备重要面试
- 每次只回复一条消息，不要分段
"""
        else:
            system_prompt = base_info

        return system_prompt

    def _detect_intent(self, message: str, context: Dict) -> str:
        """检测用户意图"""
        message_lower = message.lower()

        # 简单的关键词匹配（可以升级为更复杂的NLP模型）
        if any(word in message_lower for word in ['学习', '任务', '练习', '知识']):
            return "learning"
        elif any(word in message_lower for word in ['简历', '上传', '个性化', '定制']):
            return "personalized"
        elif any(word in message_lower for word in ['面试', '模拟', '测试']):
            return "interview"
        elif any(word in message_lower for word in ['反馈', '建议', '改进']):
            return "feedback"
        elif any(word in message_lower for word in ['帮助', '功能', '介绍', '怎么用']):
            return "help"
        else:
            return "general"

    def _generate_recommendations(self, intent: str, context: Dict, db: Session) -> List[Dict]:
        """生成功能推荐"""
        recommendations = []

        if intent == "learning":
            recommendations.append({
                "type": "action",
                "title": "开始学习任务",
                "description": "完成专业学习任务，提升知识水平",
                "action": "navigate",
                "path": "/tasks"
            })
        elif intent == "personalized":
            recommendations.append({
                "type": "action",
                "title": "上传简历",
                "description": "上传简历获取个性化面试建议",
                "action": "navigate",
                "path": "/personalized"
            })

        # 根据薄弱领域推荐
        if context.get("weak_areas"):
            weak_area = context["weak_areas"][0]
            recommendations.append({
                "type": "suggestion",
                "title": f"加强{weak_area['area']}练习",
                "description": f"你在{weak_area['area']}方面得分较低，建议多练习",
                "action": "practice",
                "area": weak_area["area"]
            })

        return recommendations

    def _get_suggested_actions(self, intent: str) -> List[str]:
        """获取建议操作"""
        actions_map = {
            "learning": ["查看任务", "开始学习", "上传学习资料"],
            "personalized": ["上传简历", "查看个性化建议", "开始模拟面试"],
            "interview": ["开始模拟面试", "查看历史面试", "查看反馈"],
            "feedback": ["查看学习报告", "设置偏好", "联系支持"]
        }
        return actions_map.get(intent, ["开始对话", "查看帮助"])

    def _save_message(
            self,
            user_id: int,
            session_id: str,
            role: str,
            content: str,
            metadata: Dict,
            db: Session
    ):
        """保存消息"""
        message = ChatMessage(
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
            meta_data=metadata
        )
        db.add(message)
        db.commit()

    def _update_preferences_from_feedback(
            self,
            user_id: int,
            feedback_type: str,
            content: str,
            rating: Optional[int],
            metadata: Optional[Dict],
            db: Session
    ):
        """根据反馈更新用户偏好"""
        preference = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if not preference:
            preference = UserPreference(user_id=user_id)
            db.add(preference)

        # 分析反馈内容，更新沟通风格偏好
        if feedback_type == "chat" and rating:
            # 如果用户给出低分，可能需要调整语气
            if rating <= 2:
                # 可以分析内容，调整语气偏好
                pass

        db.commit()