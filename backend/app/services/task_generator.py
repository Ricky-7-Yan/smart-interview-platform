"""
任务生成服务：根据岗位和用户需求生成定制化任务
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.task import Task, TaskType, TaskStatus
from app.models.user import User

class TaskGenerator:
    """任务生成器：生成岗位定制化任务树"""

    def __init__(self):
        """初始化任务生成器"""
        self._llm_service = None

    @property
    def llm_service(self):
        """延迟加载LLM服务"""
        if self._llm_service is None:
            from app.services.llm_service import LLMService
            self._llm_service = LLMService()
        return self._llm_service

    # 岗位任务模板
    POSITION_TASK_TEMPLATES = {
        "产品经理": [
            {"title": "撰写产品需求文档(PRD)", "description": "针对一个功能模块撰写完整的PRD文档"},
            {"title": "设计产品原型", "description": "使用工具设计一个功能的产品原型"},
            {"title": "用户调研分析", "description": "进行用户调研并输出分析报告"},
            {"title": "竞品分析报告", "description": "深度分析3个竞品的功能和策略"}
        ],
        "算法工程师": [
            {"title": "算法设计题", "description": "选择一个常见算法问题（如两数之和、最长递增子序列或Dijkstra算法），编写一份结构清晰、逻辑严谨的技术文档，内容包括问题定义、算法思路、步骤拆解、复杂度分析和代码实现说明。要求语言简洁准确，避免歧义，使他人能轻松理解你的解决方案。"},
            {"title": "解读顶会论文", "description": "选择一篇计算机科学领域的顶会论文（如NeurIPS、ICML、ICLR等），深入阅读并撰写解读报告，包括论文背景、核心贡献、方法细节、实验结果和你的思考。要求理解论文的创新点和局限性。"},
            {"title": "算法优化实践", "description": "优化一个现有算法的性能"},
            {"title": "技术方案设计", "description": "设计一个技术方案的完整架构"}
        ],
        "运营": [
            {"title": "活动方案设计", "description": "设计一个小型促销活动方案"},
            {"title": "文案创作", "description": "撰写商品详情页文案"},
            {"title": "数据分析报告", "description": "基于数据输出运营分析报告"},
            {"title": "用户增长策略", "description": "设计一个用户拉新策略方案"}
        ],
        "Java开发工程师": [
            {"title": "Spring Boot项目搭建", "description": "搭建一个Spring Boot项目并实现基础功能"},
            {"title": "微服务架构设计", "description": "设计一个微服务架构方案"},
            {"title": "数据库优化实践", "description": "对现有数据库进行优化"},
            {"title": "API接口设计", "description": "设计一套RESTful API接口"}
        ],
        "Python开发工程师": [
            {"title": "Django/FastAPI项目开发", "description": "使用Django或FastAPI开发一个Web应用"},
            {"title": "数据处理与分析", "description": "使用pandas处理数据并进行分析"},
            {"title": "爬虫项目实践", "description": "开发一个数据爬虫项目"},
            {"title": "自动化测试", "description": "编写自动化测试脚本"}
        ],
        "前端开发工程师": [
            {"title": "React/Vue项目搭建", "description": "搭建一个React或Vue项目"},
            {"title": "组件库开发", "description": "开发一套可复用的组件库"},
            {"title": "性能优化实践", "description": "对前端项目进行性能优化"},
            {"title": "响应式设计实现", "description": "实现移动端适配"}
        ],
        "Android开发工程师": [
            {"title": "Android项目开发", "description": "开发一个Android应用"},
            {"title": "Material Design实现", "description": "使用Material Design设计规范"},
            {"title": "性能优化", "description": "优化应用启动速度和内存使用"},
            {"title": "架构模式实践", "description": "使用MVP或MVVM架构"}
        ],
        "iOS开发工程师": [
            {"title": "iOS项目开发", "description": "开发一个iOS应用"},
            {"title": "SwiftUI实践", "description": "使用SwiftUI构建界面"},
            {"title": "性能优化", "description": "优化应用性能"},
            {"title": "架构设计", "description": "设计应用架构"}
        ],
        "测试工程师": [
            {"title": "测试用例设计", "description": "设计完整的测试用例"},
            {"title": "自动化测试框架搭建", "description": "搭建自动化测试框架"},
            {"title": "性能测试实践", "description": "进行性能测试并输出报告"},
            {"title": "测试工具使用", "description": "熟练使用常用测试工具"}
        ],
        "运维工程师": [
            {"title": "服务器配置管理", "description": "配置和管理服务器"},
            {"title": "容器化部署", "description": "使用Docker进行容器化部署"},
            {"title": "CI/CD流程搭建", "description": "搭建持续集成和部署流程"},
            {"title": "监控系统搭建", "description": "搭建监控和告警系统"}
        ]
    }

    def generate_position_tasks(self, user: User, position: str, count: int = 4, db: Session = None) -> List[Task]:
        """
        为用户生成岗位定制化任务

        Args:
            user: 用户对象
            position: 目标岗位
            count: 生成任务数量
            db: 数据库会话

        Returns:
            任务列表
        """
        tasks = []
        templates = self.POSITION_TASK_TEMPLATES.get(position, [])

        # 如果没有模板，使用LLM生成
        if not templates:
            try:
                templates = self._generate_tasks_with_llm(position, count)
            except Exception as e:
                print(f"LLM生成任务失败: {e}，使用默认模板")
                templates = [{"title": f"{position}相关任务{i+1}", "description": f"学习{position}相关内容"} for i in range(count)]

        # 使用LLM为每个任务生成详细描述
        for template in templates[:count]:
            try:
                # 为任务生成详细描述
                detailed_description = self._generate_detailed_task_description(
                    template["title"],
                    template.get("description", ""),
                    position
                )

                task = Task(
                    user_id=user.id,
                    task_type=TaskType.POSITION_BASED,
                    title=template["title"],
                    description=detailed_description,
                    position_category=position,
                    difficulty_level=3,
                    experience_reward=20,
                    status=TaskStatus.PENDING
                )
                tasks.append(task)
                if db:
                    db.add(task)
            except Exception as e:
                print(f"生成任务详细描述失败: {e}，使用模板描述")
                # 如果生成失败，使用模板描述
                task = Task(
                    user_id=user.id,
                    task_type=TaskType.POSITION_BASED,
                    title=template["title"],
                    description=template.get("description", ""),
                    position_category=position,
                    difficulty_level=3,
                    experience_reward=20,
                    status=TaskStatus.PENDING
                )
                tasks.append(task)
                if db:
                    db.add(task)

        if db:
            db.commit()

        return tasks

    def _generate_detailed_task_description(self, title: str, base_description: str, position: str) -> str:
        """使用LLM生成详细的任务描述"""
        try:
            # 特殊处理算法设计题和论文阅读任务
            if "算法设计" in title or "算法" in title and "设计" in title:
                prompt = f"""
任务标题：{title}
基础描述：{base_description}

请为这个算法设计任务生成一份详细的任务描述，包括：
1. 具体选择一个算法问题（如两数之和、最长递增子序列、Dijkstra算法、快速排序等）
2. 详细说明需要完成的内容：
   - 问题定义和背景
   - 算法思路和设计
   - 步骤拆解
   - 时间复杂度分析
   - 空间复杂度分析
   - 代码实现说明（包括关键代码片段）
3. 输出要求：结构清晰、逻辑严谨的技术文档
4. 语言要求：简洁准确，避免歧义

请直接返回详细的任务描述，不要使用编号或列表格式，用自然语言描述。
"""
            elif "论文" in title or "解读" in title:
                prompt = f"""
任务标题：{title}
基础描述：{base_description}

请为这个论文阅读任务生成一份详细的任务描述，包括：
1. 选择一篇真实的计算机科学领域顶会论文（如NeurIPS、ICML、ICLR、CVPR、ACL等）
2. 提供论文的完整信息：
   - 论文标题（真实的论文标题）
   - 作者和发表会议/期刊
   - 论文摘要（200-300字）
   - 核心贡献点（3-5个要点）
   - 主要方法概述（100-200字）
3. 要求用户完成的内容：
   - 深入阅读论文全文
   - 理解论文的创新点和贡献
   - 分析方法的优缺点
   - 撰写解读报告（包括背景、方法、实验、思考）

请直接返回详细的任务描述，包括一篇真实论文的完整信息，不要使用编号或列表格式，用自然语言描述。
"""
            else:
                prompt = f"""
任务标题：{title}
基础描述：{base_description}
目标岗位：{position}

请为这个任务生成一份详细的任务描述，包括：
1. 任务的具体要求和目标
2. 需要完成的具体步骤
3. 输出成果的要求
4. 评估标准

请直接返回详细的任务描述，不要使用编号或列表格式，用自然语言描述，要求详细具体，至少200字。
"""

            response = self.llm_service.generate(prompt, temperature=0.7, max_tokens=1000)

            # 如果响应太短，使用基础描述
            if len(response) < 50:
                return base_description if base_description else f"完成{title}相关任务"

            return response.strip()
        except Exception as e:
            print(f"生成详细任务描述失败: {e}")
            return base_description if base_description else f"完成{title}相关任务"

    def generate_remedial_task(self, weakness: str, user: User, db: Session) -> Task:
        """
        根据面试弱点生成补学任务

        Args:
            weakness: 识别的弱点
            user: 用户对象
            db: 数据库会话

        Returns:
            补学任务
        """
        # 获取用户的主要岗位
        target_positions = user.target_positions
        if target_positions and isinstance(target_positions, list) and len(target_positions) > 0:
            primary_position = target_positions[0]
        else:
            primary_position = ""

        try:
            task_data = self.llm_service.generate_remedial_task(weakness, primary_position)
        except Exception as e:
            print(f"LLM生成补学任务失败: {e}，使用默认模板")
            task_data = {
                "title": f"补学任务：{weakness}",
                "description": f"针对弱点'{weakness}'的专项训练",
                "resources": [f"学习资源：关于{weakness}"],
                "verification": "完成练习并通过验证"
            }

        task = Task(
            user_id=user.id,
            task_type=TaskType.REMEDIAL,
            title=task_data.get("title", f"补学任务：{weakness}"),
            description=task_data.get("description", ""),
            position_category=primary_position,
            difficulty_level=2,
            experience_reward=15,
            status=TaskStatus.PENDING
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        return task

    def _generate_tasks_with_llm(self, position: str, count: int) -> List[Dict]:
        """使用LLM生成任务模板"""
        prompt = f"""
目标岗位：{position}

请生成{count}个与该岗位相关的学习任务，每个任务包括：
1. 任务标题
2. 任务描述（具体要做什么，要求详细具体，至少100字）

返回JSON数组格式：
[
    {{"title": "任务标题1", "description": "详细的任务描述1"}},
    {{"title": "任务标题2", "description": "详细的任务描述2"}}
]
"""
        try:
            response = self.llm_service.generate(prompt, temperature=0.7, max_tokens=2000)
            import json
            return json.loads(response)
        except Exception as e:
            print(f"解析LLM响应失败: {e}")
            return [{"title": f"{position}相关任务{i+1}", "description": f"学习{position}相关内容"} for i in range(count)]