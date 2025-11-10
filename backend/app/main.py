"""
FastAPI主应用：定义API路由和中间件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import engine, Base
from app.api import auth, tasks, interviews, ai_service, chat, resume
from app.config import settings

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="智能面试学习平台 API",
    description="基于LLM的智能面试学习系统",
    version="1.0.0"
)

# CORS中间件：允许前端跨域访问
# 支持多个前端端口
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:5173",  # Vite默认端口
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["任务"])
app.include_router(interviews.router, prefix="/api/interviews", tags=["面试"])
app.include_router(ai_service.router, prefix="/api/ai", tags=["AI服务"])
app.include_router(chat.router, prefix="/api/chat", tags=["对话"])
app.include_router(resume.router, prefix="/api/resume", tags=["简历"])

@app.get("/")
async def root():
    """根路径"""
    return {"message": "智能面试学习平台 API", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
