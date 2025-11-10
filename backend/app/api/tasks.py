"""
任务API：处理任务相关的CRUD操作和任务生成
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict
from app.database.connection import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.models.task import Task, TaskStatus, TaskType
from app.models.interview import Interview, InterviewType, InterviewStatus
from datetime import datetime

router = APIRouter()

# 延迟初始化任务生成器
_task_generator = None

def get_task_generator():
    """获取任务生成器实例（延迟初始化）"""
    global _task_generator
    if _task_generator is None:
        from app.services.task_generator import TaskGenerator
        _task_generator = TaskGenerator()
    return _task_generator

def get_llm_service():
    """获取LLM服务实例"""
    from app.services.llm_service import LLMService
    return LLMService()

class TaskCreate(BaseModel):
    """创建任务模型"""
    title: str
    description: Optional[str] = None
    position_category: Optional[str] = None

class TaskResponse(BaseModel):
    """任务响应模型"""
    id: int
    title: str
    description: Optional[str]
    task_type: str
    status: str
    experience_reward: int
    related_interview_id: Optional[int]

    class Config:
        from_attributes = True

class NoteRequest(BaseModel):
    """笔记请求模型"""
    content: str
    selected_text: Optional[str] = None

class HighlightRequest(BaseModel):
    """标注请求模型"""
    text: str

@router.get("/", response_model=List[TaskResponse])
async def get_user_tasks(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有任务"""
    try:
        query = db.query(Task).filter(Task.user_id == current_user.id)
        if status:
            try:
                task_status = TaskStatus(status)
                query = query.filter(Task.status == task_status)
            except ValueError:
                pass
        tasks = query.order_by(Task.created_at.desc()).all()
        return tasks
    except Exception as e:
        print(f"获取任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务失败: {str(e)}")

@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除任务"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    try:
        db.delete(task)
        db.commit()
        return {"message": "任务已删除"}
    except Exception as e:
        db.rollback()
        print(f"删除任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")

@router.post("/generate-position-tasks")
async def generate_position_tasks(
    count: int = 4,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """为用户生成岗位定制化任务"""
    try:
        target_positions = current_user.target_positions
        if target_positions is None:
            target_positions = []
        elif not isinstance(target_positions, list):
            if isinstance(target_positions, str):
                target_positions = [target_positions]
            else:
                target_positions = []

        if not target_positions or len(target_positions) == 0:
            raise HTTPException(
                status_code=400,
                detail="请先在个人中心设置目标岗位"
            )

        primary_position = target_positions[0]

        task_generator = get_task_generator()
        tasks = task_generator.generate_position_tasks(
            user=current_user,
            position=primary_position,
            count=count,
            db=db
        )

        for task in tasks:
            db.refresh(task)

        return {
            "message": f"已生成{len(tasks)}个任务",
            "tasks": [{
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "experience_reward": task.experience_reward,
                "task_type": task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type),
                "status": task.status.value if hasattr(task.status, 'value') else str(task.status)
            } for task in tasks]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"生成任务失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"生成任务失败: {str(e)}")

@router.post("/{task_id}/complete")
async def complete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """完成任务"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status == TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="任务已完成")

    try:
        # 更新任务状态
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()

        # 更新用户经验值
        current_user.experience_points += task.experience_reward

        new_level = current_user.experience_points // 100 + 1
        if new_level > current_user.current_level:
            current_user.current_level = new_level

        db.commit()
        db.refresh(task)

        # 如果是岗位任务，生成关联面试
        interview_id = None
        if task.task_type == TaskType.POSITION_BASED:
            try:
                llm_service = get_llm_service()

                # 获取目标岗位
                target_positions = current_user.target_positions
                if target_positions and isinstance(target_positions, list) and len(target_positions) > 0:
                    primary_position = target_positions[0]
                else:
                    primary_position = task.position_category or "通用"

                # 生成面试问题
                print(f"开始为任务 {task.id} 生成面试问题...")
                questions = llm_service.generate_interview_questions(
                    task_description=task.description or task.title,
                    position=primary_position,
                    count=5
                )

                if not questions or len(questions) == 0:
                    print("警告：生成的面试问题为空")
                    questions = [
                        f"请介绍一下你在完成'{task.title}'任务时的思路和方法。",
                        f"在完成这个任务的过程中，你遇到了哪些挑战？",
                        f"如果让你重新完成这个任务，你会如何改进？",
                        f"这个任务对你的专业技能提升有什么帮助？",
                        f"请总结一下完成这个任务的关键要点。"
                    ]

                # 创建面试记录 - 使用枚举值而不是字符串
                interview = Interview(
                    user_id=current_user.id,
                    interview_type=InterviewType.TASK_BASED,  # 使用枚举值
                    related_task_id=task.id,
                    status=InterviewStatus.PENDING,  # 使用枚举值
                    questions=questions
                )

                db.add(interview)
                db.commit()
                db.refresh(interview)

                interview_id = interview.id
                print(f"成功创建面试记录，ID: {interview_id}")

                # 更新任务的关联面试ID
                task.related_interview_id = interview_id
                db.commit()

                return {
                    "message": "任务完成！已生成关联面试",
                    "task": {
                        "id": task.id,
                        "title": task.title,
                        "experience_reward": task.experience_reward,
                        "new_level": current_user.current_level
                    },
                    "interview_id": interview_id,
                    "questions": questions
                }
            except Exception as e:
                print(f"生成面试失败: {e}")
                import traceback
                traceback.print_exc()
                # 即使生成面试失败，任务也已经完成，返回成功但提示面试生成失败
                return {
                    "message": "任务已完成，但生成面试时出现错误",
                    "task": {
                        "id": task.id,
                        "title": task.title,
                        "experience_reward": task.experience_reward,
                        "new_level": current_user.current_level
                    },
                    "interview_id": None,
                    "error": f"生成面试失败: {str(e)}"
                }

        # 非岗位任务，直接返回完成信息
        return {
            "message": "任务完成",
            "task": {
                "id": task.id,
                "title": task.title,
                "experience_reward": task.experience_reward,
                "new_level": current_user.current_level
            },
            "interview_id": None
        }
    except Exception as e:
        db.rollback()
        print(f"完成任务失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"完成任务失败: {str(e)}")

@router.get("/{task_id}")
async def get_task_detail(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务详情"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task

@router.get("/{task_id}/notes")
async def get_task_notes(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务笔记"""
    # 验证任务存在
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 从数据库查询笔记
    from app.models.task_note import TaskNote
    notes = db.query(TaskNote).filter(
        TaskNote.task_id == task_id
    ).order_by(TaskNote.created_at.desc()).all()

    return {
        "notes": [
            {
                "id": note.id,
                "content": note.content,
                "selected_text": note.selected_text,
                "created_at": note.created_at.isoformat()
            }
            for note in notes
        ]
    }

@router.post("/{task_id}/notes")
async def save_task_note(
    task_id: int,
    note_data: NoteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """保存任务笔记"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    from app.models.task_note import TaskNote
    note = TaskNote(
        task_id=task_id,
        user_id=current_user.id,
        content=note_data.content,
        selected_text=note_data.selected_text
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    return {
        "message": "笔记已保存",
        "note": {
            "id": note.id,
            "content": note.content,
            "selected_text": note.selected_text,
            "created_at": note.created_at.isoformat()
        }
    }

@router.delete("/{task_id}/notes/{note_id}")
async def delete_task_note(
    task_id: int,
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除任务笔记"""
    from app.models.task_note import TaskNote
    note = db.query(TaskNote).filter(
        TaskNote.id == note_id,
        TaskNote.task_id == task_id,
        TaskNote.user_id == current_user.id
    ).first()

    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")

    db.delete(note)
    db.commit()
    return {"message": "笔记已删除"}

@router.get("/{task_id}/highlights")
async def get_task_highlights(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务标注"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    from app.models.task_highlight import TaskHighlight
    highlights = db.query(TaskHighlight).filter(
        TaskHighlight.task_id == task_id
    ).order_by(TaskHighlight.created_at.desc()).all()

    return {
        "highlights": [
            {
                "id": highlight.id,
                "text": highlight.text,
                "created_at": highlight.created_at.isoformat()
            }
            for highlight in highlights
        ]
    }

@router.post("/{task_id}/highlights")
async def save_task_highlight(
    task_id: int,
    highlight_data: HighlightRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """保存任务标注"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    from app.models.task_highlight import TaskHighlight
    highlight = TaskHighlight(
        task_id=task_id,
        user_id=current_user.id,
        text=highlight_data.text
    )
    db.add(highlight)
    db.commit()
    db.refresh(highlight)

    return {
        "message": "标注已保存",
        "highlight": {
            "id": highlight.id,
            "text": highlight.text,
            "created_at": highlight.created_at.isoformat()
        }
    }

@router.delete("/{task_id}/highlights/{highlight_id}")
async def delete_task_highlight(
    task_id: int,
    highlight_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除任务标注"""
    from app.models.task_highlight import TaskHighlight
    highlight = db.query(TaskHighlight).filter(
        TaskHighlight.id == highlight_id,
        TaskHighlight.task_id == task_id,
        TaskHighlight.user_id == current_user.id
    ).first()

    if not highlight:
        raise HTTPException(status_code=404, detail="标注不存在")

    db.delete(highlight)
    db.commit()
    return {"message": "标注已删除"}

@router.get("/{task_id}/leetcode")
async def get_leetcode_problem(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取LeetCode题目（用于算法任务）"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {
        "title": "两数之和",
        "difficulty": "简单",
        "description": "给定一个整数数组 nums 和一个整数目标值 target，请你在该数组中找出 和为目标值 target  的那 两个 整数，并返回它们的数组下标。你可以假设每种输入只会对应一个答案。但是，数组中同一个元素在答案里不能重复出现。",
        "examples": [
            {
                "input": "nums = [2,7,11,15], target = 9",
                "output": "[0,1]",
                "explanation": "因为 nums[0] + nums[1] == 9 ，返回 [0, 1] 。"
            },
            {
                "input": "nums = [3,2,4], target = 6",
                "output": "[1,2]",
                "explanation": ""
            }
        ],
        "constraints": [
            "2 <= nums.length <= 10^4",
            "-10^9 <= nums[i] <= 10^9",
            "-10^9 <= target <= 10^9",
            "只会存在一个有效答案"
        ],
        "leetcodeUrl": "https://leetcode.cn/problems/two-sum/"
    }