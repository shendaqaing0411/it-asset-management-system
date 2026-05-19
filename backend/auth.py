# 认证模块：JWT token 签发/验证、bcrypt 密码哈希、请求鉴权依赖
# 权限引擎：require_permission(code) 从角色表动态读取权限码

import os
import json
import secrets
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
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


def _get_user_role(user: dict) -> dict:
    """获取用户所属的角色对象（含 permissions 和 scope 字段）。
    优先用 role_id，其次用 role 字段匹配角色名（兼容旧数据）"""
    db = get_db()
    role = None
    role_id = user.get("role_id")
    if role_id:
        role = db.execute("SELECT * FROM roles WHERE id = ?", (role_id,)).fetchone()
    if not role:
        # 兼容旧字段：按 role 字符串匹配内置角色
        role_name_map = {
            "super_admin": "超级管理员", "admin": "超级管理员",
            "asset_admin": "资产管理员", "dept_manager": "部门主管",
            "user": "普通用户", "auditor": "审计员",
        }
        name = role_name_map.get(user.get("role", ""), user.get("role", ""))
        role = db.execute("SELECT * FROM roles WHERE name = ?", (name,)).fetchone()
    db.close()
    if not role:
        raise HTTPException(status_code=403, detail="用户未分配角色，请联系管理员")
    return dict(role)


def require_permission(code: str):
    """权限码检查依赖：验证当前用户角色是否拥有指定权限码。
    用法：user: dict = Depends(require_permission("asset:create"))"""
    def _check(user: dict = Depends(get_current_user)):
        role = _get_user_role(user)
        perms = json.loads(role["permissions"] or "[]")
        if code not in perms:
            raise HTTPException(status_code=403, detail="权限不足")
        return user
    return _check


def require_role(*roles: str):
    """[deprecated] 保留向后兼容，新代码请用 require_permission(code)。
    验证当前用户角色名称匹配（从角色表读取）。"""
    def _check(user: dict = Depends(get_current_user)):
        role = _get_user_role(user)
        if role["name"] not in roles:
            raise HTTPException(status_code=403, detail="权限不足")
        return user
    return _check


def require_dept_scope():
    """数据范围过滤器：从角色表的 scope 字段读取，返回 SQL 过滤条件。
    - all → None（全量数据）
    - dept → {"dept_id": user.dept_id}
    - self → {"user_id": user.id}
    用法：scope: Optional[dict] = Depends(require_dept_scope())"""
    def _scope(user: dict = Depends(get_current_user)) -> Optional[dict]:
        role = _get_user_role(user)
        scope = role.get("scope", "all")
        if scope == "all":
            return None
        if scope == "dept":
            dept_id = user.get("dept_id")
            if not dept_id:
                raise HTTPException(status_code=403, detail="该角色需要关联部门，请联系管理员设置")
            return {"dept_id": dept_id}
        if scope == "self":
            return {"user_id": user["id"]}
        return None
    return _scope
