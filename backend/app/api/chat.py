"""
对话API：提供AI对话接口
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
from app.database.connection import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.chat import ChatSession
from app.services.chat_service import ChatService

router = APIRouter()

# 延迟初始化服务
_chat_service = None


def get_chat_service():
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service


class ChatMessageRequest(BaseModel):
    """对话消息请求"""
    message: str
    session_id: Optional[str] = None
    context_type: str = "general"  # general, learning, personalized


class ChatMessageResponse(BaseModel):
    """对话消息响应"""
    response: str
    session_id: str
    intent: str
    recommendations: List[Dict] = []
    suggested_actions: List[str] = []


class SaveSessionRequest(BaseModel):
    """保存会话请求"""
    session_id: str
    name: str
    context_type: str


class FeedbackRequest(BaseModel):
    """反馈请求"""
    feedback_type: str
    content: str
    rating: Optional[int] = None
    metadata: Optional[Dict] = None


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
        request: ChatMessageRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """发送消息并获取AI回复"""
    try:
        chat_service = get_chat_service()

        # 获取或创建会话
        if not request.session_id:
            session_id = chat_service.get_or_create_session(
                current_user.id,
                request.context_type,
                db
            )
        else:
            session_id = request.session_id

        # 处理消息
        response, metadata = chat_service.process_user_message(
            current_user.id,
            request.message,
            session_id,
            request.context_type,
            db
        )

        return {
            "response": response,
            "session_id": session_id,
            "intent": metadata.get("intent", "general"),
            "recommendations": metadata.get("recommendations", []),
            "suggested_actions": metadata.get("suggested_actions", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理消息失败: {str(e)}")


@router.get("/greeting")
async def get_greeting(
        context_type: str = "general",
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取欢迎消息"""
    try:
        chat_service = get_chat_service()
        greeting = chat_service.generate_greeting(current_user, db, context_type)

        # 创建新会话
        session_id = chat_service.get_or_create_session(
            current_user.id,
            context_type,
            db
        )

        # 保存欢迎消息
        from app.models.chat import ChatMessage
        welcome_msg = ChatMessage(
            user_id=current_user.id,
            session_id=session_id,
            role="assistant",
            content=greeting,
            meta_data={"type": "greeting"}
        )
        db.add(welcome_msg)
        db.commit()

        return {
            "message": greeting,
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成欢迎消息失败: {str(e)}")


@router.get("/history/{session_id}")
async def get_history(
        session_id: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取对话历史"""
    try:
        chat_service = get_chat_service()
        history = chat_service.get_conversation_history(session_id, db=db)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")


@router.get("/sessions")
async def get_sessions(
        context_type: Optional[str] = None,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取用户的会话列表"""
    try:
        query = db.query(ChatSession).filter(ChatSession.user_id == current_user.id)
        if context_type:
            query = query.filter(ChatSession.context_type == context_type)

        sessions = query.order_by(ChatSession.updated_at.desc()).all()

        return {
            "sessions": [
                {
                    "id": s.id,
                    "session_id": s.session_id,
                    "name": s.summary or "未命名会话",
                    "context_type": s.context_type,
                    "created_at": s.created_at.isoformat(),
                    "updated_at": s.updated_at.isoformat()
                }
                for s in sessions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.post("/save-session")
async def save_session(
        request: SaveSessionRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """保存会话（设置名称）"""
    try:
        session = db.query(ChatSession).filter(
            ChatSession.session_id == request.session_id,
            ChatSession.user_id == current_user.id
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        session.summary = request.name
        db.commit()

        return {"message": "会话已保存"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存会话失败: {str(e)}")


@router.post("/feedback")
async def submit_feedback(
        request: FeedbackRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """提交用户反馈"""
    try:
        chat_service = get_chat_service()
        chat_service.collect_feedback(
            current_user.id,
            request.feedback_type,
            request.content,
            request.rating,
            request.metadata,
            db
        )
        return {"message": "反馈已收到，感谢您的建议！"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交反馈失败: {str(e)}")


@router.post("/update-analytics/{interview_id}")
async def update_analytics(
        interview_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """根据面试结果更新学习分析"""
    try:
        chat_service = get_chat_service()
        chat_service.update_learning_analytics(current_user.id, interview_id, db)
        return {"message": "分析已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新分析失败: {str(e)}")