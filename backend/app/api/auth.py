"""
认证API：处理用户注册、登录、JWT token
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.database.connection import get_db
from app.models.user import User
from app.models.ranking import TitleBenefit
from app.config import settings

router = APIRouter()
security = HTTPBearer()

class UserRegister(BaseModel):
    """用户注册模型"""
    username: str
    email: EmailStr
    password: str
    target_positions: List[str] = []

    @validator('username')
    def validate_username(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('用户名不能为空')
        if len(v) < 2:
            raise ValueError('用户名长度至少为2个字符')
        if len(v) > 50:
            raise ValueError('用户名长度不能超过50个字符')
        return v.strip()

    @validator('password')
    def validate_password(cls, v):
        if not v or len(v) < 6:
            raise ValueError('密码长度至少为6位')
        if len(v) > 100:
            raise ValueError('密码长度不能超过100位')
        return v

    @validator('target_positions')
    def validate_target_positions(cls, v):
        if not v or len(v) == 0:
            raise ValueError('请至少选择一个目标岗位')
        if len(v) > 10:
            raise ValueError('最多只能选择10个岗位')
        return v

class UserLogin(BaseModel):
    """用户登录模型"""
    email: EmailStr
    password: str

class UpdatePositionsRequest(BaseModel):
    """更新岗位请求模型"""
    target_positions: List[str]

class Token(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str = "bearer"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码（使用原生 bcrypt）"""
    try:
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_password, hashed_password)
    except Exception as e:
        print(f"密码验证错误: {e}")
        return False

def get_password_hash(password: str) -> str:
    """加密密码（使用原生 bcrypt）"""
    try:
        if isinstance(password, str):
            password = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password, salt)
        return hashed.decode('utf-8')
    except Exception as e:
        print(f"密码加密错误: {e}")
        raise

def create_access_token(data: dict, expires_delta: timedelta = None):
    """创建JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取当前登录用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        # 检查邮箱是否已存在
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="邮箱已被注册")

        # 检查用户名是否已存在
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            raise HTTPException(status_code=400, detail="用户名已被使用")

        # 加密密码
        try:
            hashed_password = get_password_hash(user_data.password)
        except Exception as e:
            print(f"密码加密错误: {e}")
            raise HTTPException(status_code=500, detail="密码加密失败，请重试")

        # 创建用户
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            target_positions=user_data.target_positions
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 生成token
        access_token = create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"注册错误: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.put("/update-positions")
async def update_positions(
    request: UpdatePositionsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户目标岗位"""
    if len(request.target_positions) == 0:
        raise HTTPException(status_code=400, detail="请至少保留一个目标岗位")

    if len(request.target_positions) > 10:
        raise HTTPException(status_code=400, detail="最多只能选择10个岗位")

    current_user.target_positions = request.target_positions
    db.commit()

    return {"message": "目标岗位已更新", "target_positions": current_user.target_positions}

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户信息"""
    title_benefit = db.query(TitleBenefit).filter(
        TitleBenefit.min_level <= current_user.current_level,
        (TitleBenefit.max_level >= current_user.current_level) | (TitleBenefit.max_level.is_(None))
    ).order_by(TitleBenefit.min_level.desc()).first()

    if title_benefit:
        current_user.title = title_benefit.title_name
        db.commit()

    # 处理 target_positions，确保返回列表格式
    target_positions = current_user.target_positions
    if target_positions is None:
        target_positions = []
    elif not isinstance(target_positions, list):
        # 如果是单个值或其他格式，转换为列表
        if isinstance(target_positions, str):
            target_positions = [target_positions]
        else:
            target_positions = []

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "target_positions": target_positions,
        "current_level": current_user.current_level,
        "experience_points": current_user.experience_points,
        "title": current_user.title,
        "benefits": title_benefit.benefits if title_benefit else {}
    }