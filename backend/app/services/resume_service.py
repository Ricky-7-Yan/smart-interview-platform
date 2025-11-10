"""
简历解析服务：解析用户上传的简历文件
"""
import os
import json
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.services.llm_service import LLMService
from app.models.resume import Resume


class ResumeService:
    """简历解析服务类"""

    def __init__(self):
        self.llm_service = LLMService()
        self.upload_dir = "uploads/resumes"

    def parse_resume(self, file_path: str, file_type: str) -> Dict:
        """解析简历文件"""
        # 读取文件内容
        if file_type == "txt":
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif file_type == "pdf":
            # 需要安装PyPDF2或pdfplumber
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    content = "\n".join([page.extract_text() for page in pdf_reader.pages])
            except:
                content = "无法解析PDF文件，请确保已安装PyPDF2"
        else:
            content = "不支持的文件类型"

        # 使用LLM解析结构化数据
        return self._extract_resume_data(content)

    def _extract_resume_data(self, raw_text: str) -> Dict:
        """从文本中提取结构化简历数据"""
        system_prompt = """你是一位专业的简历解析专家，擅长从文本中提取结构化信息。"""

        prompt = f"""
请从以下简历文本中提取结构化信息：

{raw_text[:2000]}  # 限制长度

请返回JSON格式：
{{
    "name": "姓名",
    "email": "邮箱",
    "phone": "电话",
    "education": "教育背景（学校、专业、学历）",
    "experience": "工作经历（公司、职位、时间、描述）",
    "skills": ["技能1", "技能2", ...],
    "projects": ["项目1", "项目2", ...],
    "certifications": ["证书1", "证书2", ...],
    "summary": "个人简介"
}}

如果某项信息不存在，请返回null或空数组。
"""

        response = self.llm_service.generate(prompt, system_prompt, temperature=0.3)

        try:
            return json.loads(response)
        except:
            # 如果解析失败，返回基础结构
            return {
                "name": None,
                "email": None,
                "phone": None,
                "education": None,
                "experience": None,
                "skills": [],
                "projects": [],
                "certifications": [],
                "summary": None,
                "raw_text": raw_text
            }

    def save_resume(
            self,
            user_id: int,
            file_path: str,
            file_name: str,
            file_type: str,
            parsed_data: Dict,
            raw_text: str,
            db: Session
    ) -> Resume:
        """保存简历到数据库"""
        # 将之前的简历设为非激活
        db.query(Resume).filter(
            Resume.user_id == user_id,
            Resume.is_active == 1
        ).update({"is_active": 0})

        # 创建新简历记录
        resume = Resume(
            user_id=user_id,
            file_path=file_path,
            file_name=file_name,
            file_type=file_type,
            parsed_data=parsed_data,
            raw_text=raw_text,
            is_active=1,
            version=1
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        return resume