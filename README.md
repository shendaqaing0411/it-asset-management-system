# IT 资产管理系统

轻量化本地 IT 资产进销存管理系统，基于 **Vue 3 + FastAPI + SQLite**，单文件数据库即装即用。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 (Composition API) + Element Plus + ECharts |
| 后端 | FastAPI + Pydantic v2 |
| 数据库 | SQLite (WAL 模式) |
| 认证 | JWT (HS256, 24h) + bcrypt |

## 功能模块

- **仪表盘** — 统计卡片、状态分布图、分类占比图、库存预警
- **资产管理** — 资产登记/列表/盘点、二维码生成、Excel 批量导入导出
- **库存管理** — 入库/出库/归还/调拨、库存查询、预警规则
- **维保报废** — 维修记录管理、资产报废
- **报表统计** — 资产汇总、库存统计、出入库明细
- **系统管理** — 部门/分类/仓库/供应商/用户管理、操作日志

## 下载

```bash
git clone https://github.com/shendaqaing0411/it-asset-management-system.git
cd it-asset-management-system
```

## 启动

### 方式一：开发模式（前后端分离）

```bash
# 终端1 — 启动后端
cd backend
pip install -r requirements.txt
python main.py
# 后端运行在 http://localhost:8000
# API 文档: http://localhost:8000/docs

# 终端2 — 启动前端
cd frontend
npm install
npm run dev
# 前端运行在 http://localhost:5173
```

浏览器访问 `http://localhost:5173`，默认账号 `admin` / `admin123`。

### 方式二：生产模式（单服务）

```bash
cd frontend && npm install && npm run build
cd ../backend && pip install -r requirements.txt && python main.py
```

访问 `http://localhost:8000`，前端已内嵌到后端服务。

## 关闭

- **开发模式** — 分别在两个终端按 `Ctrl+C` 停止前后端
- **生产模式** — 在终端按 `Ctrl+C` 停止后端服务
- 数据保存在 `backend/data/it_assets.db`，关闭不会丢失

## 项目结构

```
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── database.py           # 数据库初始化与连接
│   ├── auth.py               # JWT 认证
│   ├── schemas.py            # 数据模型
│   ├── requirements.txt
│   └── routers/              # API 路由
│       ├── auth.py           # 登录/登出
│       ├── assets.py         # 资产 CRUD + 导入导出
│       ├── stock.py          # 出入库/库存/预警
│       ├── repairs.py        # 维修/报废
│       ├── reports.py        # 报表统计
│       └── system.py         # 系统管理
└── frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── api/index.js      # Axios 封装
        ├── router/index.js   # 路由配置
        ├── components/       # 公共组件
        └── views/            # 页面组件
```

## 环境要求

- Python 3.9+
- Node.js 18+

## 安全

- JWT 密钥通过环境变量 `IT_ASSET_SECRET` 配置
- 密码 bcrypt 哈希存储，参数化查询防 SQL 注入
- 管理员操作后端二次校验角色

## License

MIT
