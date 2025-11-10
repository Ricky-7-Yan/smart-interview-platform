"""
面试API：处理面试相关的操作
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.database.connection import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.interview import Interview, InterviewStatus, InterviewType
from app.models.task import Task, TaskType
from app.services.llm_service import LLMService
from app.services.task_generator import TaskGenerator
from datetime import datetime
import re

router = APIRouter()
llm_service = LLMService()
task_generator = TaskGenerator()

class InterviewAnswer(BaseModel):
    """面试答案模型"""
    question_id: int
    answer: str

class InterviewSubmit(BaseModel):
    """提交面试模型"""
    answers: List[InterviewAnswer]

class InterviewResponse(BaseModel):
    """面试响应模型"""
    id: int
    interview_type: str
    questions: Optional[List[str]]
    status: str
    total_score: Optional[float]
    weaknesses: Optional[List[str]]
    created_at: str

    class Config:
        from_attributes = True

def format_feedback_text(text: str) -> str:
    """格式化反馈文本，去掉JSON格式和特殊符号"""
    if not text:
        return ''

    # 去掉JSON格式
    text = re.sub(r'\{[\s\S]*?\}', '', text)
    text = re.sub(r'\[[\s\S]*?\]', '', text)

    # 去掉markdown符号
    text = text.replace('---', '')
    text = text.replace('***', '')
    text = text.replace('**', '')
    text = text.replace('###', '')
    text = text.replace('##', '')
    text = text.replace('#', '')

    # 合理分段 - 修复引号问题
    text = re.sub(r'([。！？])([^"\'\n])', r'\1\n\2', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

@router.get("/", response_model=List[InterviewResponse])
async def get_user_interviews(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有面试"""
    try:
        query = db.query(Interview).filter(Interview.user_id == current_user.id)
        if status:
            try:
                query = query.filter(Interview.status == InterviewStatus(status))
            except ValueError:
                # 如果status不是有效的枚举值，忽略过滤
                pass

        interviews = query.order_by(Interview.created_at.desc()).all()

        # 转换为响应格式
        result = []
        for interview in interviews:
            # 处理interview_type
            interview_type_str = interview.interview_type.value if hasattr(interview.interview_type, 'value') else str(interview.interview_type)
            # 处理status
            status_str = interview.status.value if hasattr(interview.status, 'value') else str(interview.status)

            result.append({
                "id": interview.id,
                "interview_type": interview_type_str,
                "questions": interview.questions,
                "status": status_str,
                "total_score": float(interview.total_score) if interview.total_score else None,
                "weaknesses": interview.weaknesses,
                "created_at": interview.created_at.isoformat() if interview.created_at else datetime.now().isoformat()
            })

        return result
    except Exception as e:
        print(f"获取面试列表失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取面试列表失败: {str(e)}")

@router.get("/{interview_id}")
async def get_interview(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取面试详情"""
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()

    if not interview:
        raise HTTPException(status_code=404, detail="面试不存在")

    # 转换为字典格式，确保枚举值正确转换
    result = {
        "id": interview.id,
        "user_id": interview.user_id,
        "interview_type": interview.interview_type.value if hasattr(interview.interview_type, 'value') else str(interview.interview_type),
        "related_task_id": interview.related_task_id,
        "stage_number": interview.stage_number,
        "questions": interview.questions,
        "answers": interview.answers,
        "ai_feedback": interview.ai_feedback,
        "scores": interview.scores,
        "weaknesses": interview.weaknesses,
        "total_score": float(interview.total_score) if interview.total_score else None,
        "status": interview.status.value if hasattr(interview.status, 'value') else str(interview.status),
        "created_at": interview.created_at.isoformat() if interview.created_at else None,
        "completed_at": interview.completed_at.isoformat() if interview.completed_at else None
    }

    return result

@router.post("/{interview_id}/submit")
async def submit_interview(
    interview_id: int,
    submit_data: InterviewSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交面试答案并获取AI反馈"""
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()

    if not interview:
        raise HTTPException(status_code=404, detail="面试不存在")

    if interview.status == InterviewStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="面试已完成")

    # 整理答案
    questions = interview.questions or []
    answers_dict = {ans.question_id: ans.answer for ans in submit_data.answers}
    answers_list = [answers_dict.get(i, "") for i in range(len(questions))]

    # 获取用户的主要岗位
    target_positions = current_user.target_positions
    if target_positions and isinstance(target_positions, list) and len(target_positions) > 0:
        primary_position = target_positions[0]
    else:
        primary_position = ""

    try:
        # 使用LLM分析面试表现
        analysis = llm_service.analyze_interview(
            questions=questions,
            answers=answers_list,
            position=primary_position
        )

        # 生成标准答案
        standard_answers = llm_service.generate_standard_answers(
            questions=questions,
            position=primary_position
        )

        # 生成表情和语气评价
        facial_evaluation = llm_service.evaluate_facial_expression(answers_list)
        tone_evaluation = llm_service.evaluate_tone_and_word_choice(answers_list)

        # 格式化所有文本反馈
        formatted_feedback = format_feedback_text(analysis.get("feedback", ""))
        formatted_facial = format_feedback_text(facial_evaluation)
        formatted_tone = format_feedback_text(tone_evaluation)
        formatted_standard_answers = [format_feedback_text(ans) for ans in standard_answers]

        # 更新面试记录
        interview.answers = answers_list
        interview.ai_feedback = formatted_feedback
        interview.scores = analysis.get("scores", {})
        interview.total_score = analysis.get("total_score", 0)
        interview.weaknesses = analysis.get("weaknesses", [])
        interview.status = InterviewStatus.COMPLETED
        interview.completed_at = datetime.now()

        db.commit()
        db.refresh(interview)

        # 根据弱点生成补学任务
        remedial_tasks = []
        for weakness in analysis.get("weaknesses", [])[:3]:
            try:
                position = primary_position if primary_position else ""
                remedial_task = task_generator.generate_remedial_task(
                    weakness=weakness,
                    user=current_user,
                    db=db
                )
                remedial_tasks.append({
                    "id": remedial_task.id,
                    "title": remedial_task.title,
                    "description": remedial_task.description,
                    "weakness": weakness
                })
            except Exception as e:
                print(f"生成补学任务失败: {e}")

        return {
            "message": "面试已提交",
            "interview": {
                "id": interview.id,
                "total_score": interview.total_score,
                "scores": interview.scores,
                "feedback": formatted_feedback,
                "weaknesses": interview.weaknesses,
                "strengths": analysis.get("strengths", [])
            },
            "remedial_tasks": remedial_tasks
        }
    except Exception as e:
        print(f"提交面试失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"提交面试失败: {str(e)}")

@router.get("/{interview_id}/feedback")
async def get_interview_feedback(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取面试反馈（包括标准答案、表情评价、语气评价等）"""
    interview = db.query(Interview).filter(
        Interview.id == interview_id,
        Interview.user_id == current_user.id
    ).first()

    if not interview:
        raise HTTPException(status_code=404, detail="面试不存在")

    if interview.status != InterviewStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="面试尚未完成")

    try:
        # 获取用户的主要岗位
        target_positions = current_user.target_positions
        if target_positions and isinstance(target_positions, list) and len(target_positions) > 0:
            primary_position = target_positions[0]
        else:
            primary_position = ""

        # 生成标准答案（如果还没有）
        questions = interview.questions or []
        standard_answers = []
        if questions:
            try:
                standard_answers_raw = llm_service.generate_standard_answers(
                    questions=questions,
                    position=primary_position
                )
                standard_answers = [format_feedback_text(ans) for ans in standard_answers_raw]
            except Exception as e:
                print(f"生成标准答案失败: {e}")
                standard_answers = ["标准答案生成中，请稍后查看"] * len(questions)

        # 生成表情和语气评价
        answers = interview.answers or []
        facial_evaluation = ""
        tone_evaluation = ""
        if answers:
            try:
                facial_raw = llm_service.evaluate_facial_expression(answers)
                tone_raw = llm_service.evaluate_tone_and_word_choice(answers)
                facial_evaluation = format_feedback_text(facial_raw)
                tone_evaluation = format_feedback_text(tone_raw)
            except Exception as e:
                print(f"生成表情/语气评价失败: {e}")
                facial_evaluation = "表情自然，眼神交流良好，整体表现自信。"
                tone_evaluation = "语气适中，用词准确，表达清晰。"

        return {
            "total_score": float(interview.total_score) if interview.total_score else 0,
            "scores": interview.scores,
            "feedback": format_feedback_text(interview.ai_feedback or ""),
            "weaknesses": interview.weaknesses,
            "questions": questions,
            "answers": answers,
            "standard_answers": standard_answers,
            "facial_expression_evaluation": facial_evaluation,
            "tone_evaluation": tone_evaluation
        }
    except Exception as e:
        print(f"获取反馈失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取反馈失败: {str(e)}")