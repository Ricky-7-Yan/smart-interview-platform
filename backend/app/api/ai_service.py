"""
AI服务API：提供RAG检索、知识问答等AI功能
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from app.database.connection import get_db
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter()

# 延迟初始化RAG服务
_rag_service = None
_llm_service = None

def get_rag_service():
    """获取RAG服务实例（延迟初始化）"""
    global _rag_service
    if _rag_service is None:
        from app.services.rag_service import RAGService
        _rag_service = RAGService()
    return _rag_service

def get_llm_service():
    """获取LLM服务实例（延迟初始化）"""
    global _llm_service
    if _llm_service is None:
        from app.services.llm_service import LLMService
        _llm_service = LLMService()
    return _llm_service

class QuestionRequest(BaseModel):
    """问题请求模型"""
    question: str
    position_category: str = None

class AnswerResponse(BaseModel):
    """答案响应模型"""
    answer: str
    sources: List[dict] = []

@router.post("/ask", response_model=AnswerResponse)
async def ask_question(
    request: QuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """使用RAG回答问题"""
    try:
        rag_service = get_rag_service()

        # 获取用户的主要岗位
        target_positions = current_user.target_positions
        if target_positions and isinstance(target_positions, list) and len(target_positions) > 0:
            primary_position = target_positions[0]
        else:
            primary_position = request.position_category or ""

        answer = rag_service.generate_answer_with_context(
            question=request.question,
            position_category=primary_position,
            db=db
        )

        # 检索相关文档
        sources = rag_service.search_knowledge(
            query=request.question,
            position_category=primary_position,
            db=db,
            top_k=3
        )

        return {
            "answer": answer,
            "sources": sources
        }
    except Exception as e:
        print(f"RAG服务错误: {e}")
        # 如果RAG失败，使用LLM直接回答
        llm_service = get_llm_service()

        target_positions = current_user.target_positions
        if target_positions and isinstance(target_positions, list) and len(target_positions) > 0:
            primary_position = target_positions[0]
        else:
            primary_position = request.position_category or "通用"

        answer = llm_service.generate(
            f"问题：{request.question}\n请给出专业回答。",
            f"你是一位专业的面试导师，擅长回答{primary_position}相关问题。"
        )
        return {
            "answer": answer,
            "sources": []
        }

@router.post("/generate-questions")
async def generate_custom_questions(
    task_description: str,
    count: int = 5,
    current_user: User = Depends(get_current_user)
):
    """生成定制化面试问题"""
    llm_service = get_llm_service()

    # 获取用户的主要岗位
    target_positions = current_user.target_positions
    if target_positions and isinstance(target_positions, list) and len(target_positions) > 0:
        primary_position = target_positions[0]
    else:
        primary_position = ""

    questions = llm_service.generate_interview_questions(
        task_description=task_description,
        position=primary_position,
        count=count
    )
    return {"questions": questions}