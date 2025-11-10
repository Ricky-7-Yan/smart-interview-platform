"""
简历API：处理简历上传和解析
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import os
import uuid
from app.database.connection import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.services.resume_service import ResumeService

router = APIRouter()

# 延迟初始化服务
_resume_service = None


def get_resume_service():
    global _resume_service
    if _resume_service is None:
        _resume_service = ResumeService()
    return _resume_service


class ResumeResponse(BaseModel):
    """简历响应"""
    id: int
    file_name: str
    parsed_data: dict
    created_at: str


@router.post("/upload")
async def upload_resume(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """上传并解析简历"""
    try:
        resume_service = get_resume_service()

        # 检查文件类型
        file_type = file.filename.split('.')[-1].lower()
        if file_type not in ['pdf', 'docx', 'txt']:
            raise HTTPException(status_code=400, detail="不支持的文件类型，请上传PDF、DOCX或TXT文件")

        # 创建上传目录
        upload_dir = resume_service.upload_dir
        os.makedirs(upload_dir, exist_ok=True)

        # 保存文件
        file_id = str(uuid.uuid4())
        file_path = os.path.join(upload_dir, f"{current_user.id}_{file_id}.{file_type}")

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # 解析简历
        parsed_data = resume_service.parse_resume(file_path, file_type)

        # 保存到数据库
        resume = resume_service.save_resume(
            current_user.id,
            file_path,
            file.filename,
            file_type,
            parsed_data,
            parsed_data.get("raw_text", ""),
            db
        )

        return {
            "id": resume.id,
            "file_name": resume.file_name,
            "parsed_data": resume.parsed_data,
            "created_at": resume.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传简历失败: {str(e)}")


@router.get("/")
async def get_resume(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取用户当前激活的简历"""
    from app.models.resume import Resume

    resume = db.query(Resume).filter(
        Resume.user_id == current_user.id,
        Resume.is_active == 1
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="未找到简历")

    return {
        "id": resume.id,
        "file_name": resume.file_name,
        "parsed_data": resume.parsed_data,
        "created_at": resume.created_at.isoformat()
    }


@router.post("/generate-questions")
async def generate_resume_questions(
        count: int = 5,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """基于简历生成面试问题"""
    try:
        from app.models.resume import Resume
        from app.models.user_preference import UserPreference
        from app.services.personalization_service import PersonalizationService

        # 获取简历
        resume = db.query(Resume).filter(
            Resume.user_id == current_user.id,
            Resume.is_active == 1
        ).first()

        if not resume:
            raise HTTPException(status_code=404, detail="请先上传简历")

        # 获取用户偏好
        preference = db.query(UserPreference).filter(
            UserPreference.user_id == current_user.id
        ).first()

        # 生成问题
        personalization_service = PersonalizationService()
        questions = personalization_service.generate_personalized_questions(
            resume.parsed_data or {},
            preference,
            count
        )

        return {"questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成问题失败: {str(e)}")