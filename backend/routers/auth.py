# 认证路由：登录、登出、获取当前用户信息

from fastapi import APIRouter, Depends
from database import get_db
from auth import hash_password, verify_password, create_token, get_current_user, decode_token
from schemas import LoginReq, Response

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login")
def login(req: LoginReq):
    """用户登录：验证用户名密码，返回 JWT 令牌与用户信息"""
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (req.username,)).fetchone()
    db.close()
    if not user or not verify_password(req.password, user["password"]):
        return Response(code=1, message="用户名或密码错误").model_dump()
    if user["status"] != "active":
        return Response(code=1, message="账号已被禁用").model_dump()
    token = create_token(user["id"], user["username"], user["role"])
    return Response(data={
        "token": token,
        "user": {"id": user["id"], "username": user["username"], "real_name": user["real_name"], "role": user["role"]}
    }, message="登录成功").model_dump()


@router.post("/logout")
def logout():
    """用户登出（前端清除 token 即可，后端保留接口）"""
    return Response(message="已登出").model_dump()


@router.get("/current")
def current(user: dict = Depends(get_current_user)):
    """获取当前登录用户的详细信息"""
    return Response(data={
        "id": user["id"], "username": user["username"],
        "real_name": user["real_name"], "role": user["role"]
    }).model_dump()
