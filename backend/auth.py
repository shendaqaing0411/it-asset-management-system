# 认证模块：JWT token 签发/验证、bcrypt 密码哈希、请求鉴权依赖

import os
import secrets
import jwt
import bcrypt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, Header
from database import get_db

# JWT 密钥：优先从环境变量读取，否则随机生成（每次重启会变化，生产环境须配置环境变量）
SECRET_KEY = os.getenv("IT_ASSET_SECRET", secrets.token_hex(32))
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    """bcrypt 哈希密码"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """验证明文密码与哈希值是否匹配"""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: int, username: str, role: str) -> str:
    """签发 JWT 登录令牌，包含用户身份信息，有效期 24 小时"""
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """解析 JWT 令牌，校验签名与过期时间"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="登录已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的登录凭证")


def get_current_user(authorization: str = Header(...)):
    """FastAPI 依赖注入：从 Authorization 头提取当前登录用户"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization[7:]
    payload = decode_token(token)
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (payload["user_id"],)).fetchone()
    db.close()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return dict(user)


def require_role(*roles: str):
    """返回一个依赖函数，验证当前用户是否拥有指定角色之一。
    用法：user: dict = Depends(require_role("super_admin", "asset_admin"))"""
    def _check(user: dict = Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="权限不足")
        return user
    return _check
