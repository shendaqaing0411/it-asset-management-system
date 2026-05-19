# IT资产管理系统 - 主入口
# FastAPI 应用启动、中间件配置、路由注册、静态文件挂载

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import init_db
from routers import auth, assets, stock, repairs, reports, system, dict, scraps, approvals, notifications, depreciation, roles


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 应用生命周期管理：启动时初始化数据库
    init_db()
    print("数据库初始化完成")
    yield


app = FastAPI(title="IT资产管理系统", version="1.0", lifespan=lifespan)

# CORS 跨域配置，允许前端开发服务器访问
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册各模块路由
app.include_router(auth.router)
app.include_router(assets.router)
app.include_router(stock.router)
app.include_router(repairs.router)
app.include_router(reports.router)
app.include_router(system.router)
app.include_router(dict.router)
app.include_router(scraps.router)
app.include_router(approvals.router)
app.include_router(notifications.router)
app.include_router(depreciation.router)
app.include_router(roles.router)

# 生产模式：挂载前端构建产物为静态文件
frontend_dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
