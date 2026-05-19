# IT 资产管理系统 3.0

轻量化本地 IT 资产全生命周期管理系统，基于 **Vue 3 + FastAPI + SQLite**，单文件数据库即装即用。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 (Composition API) + Element Plus + ECharts |
| 后端 | FastAPI + Pydantic v2 |
| 数据库 | SQLite (WAL 模式) |
| 认证 | JWT (HS256, 24h) + bcrypt |

## 功能模块

### 核心业务
- **仪表盘** — 统计卡片、状态分布图、分类占比图、保修预警、库存预警
- **资产管理** — 资产登记/列表/盘点、二维码生成、Excel 批量导入导出、**资产时间线**
- **库存管理** — 入库/出库/归还/调拨、库存查询、预警规则、**领用审批流（申请→审批→出库）**
- **维保管理** — 维修记录管理（4 种维修类型 + 返修入库确认）、**报废管理（自然老化/人为损坏分类校验）**
- **报表统计** — 资产汇总、库存统计、出入库明细、**折旧报表（直线法/一次性，按分类配置残值率+使用年限，分类汇总）**

### 系统支撑
- **通知中心** — 铃铛组件实时推送，覆盖审批/维修/保修/库存 4 种通知类型
- **数据字典** — 自定义字段管理（文本/数字/下拉/日期），资产表单动态渲染
- **角色权限** — 自定义 RBAC（用户 → 角色 → 权限码），38 个细粒度权限码覆盖 10 大模块，支持 all/dept/self 三级数据范围，内置 5 个预设角色
- **系统管理** — 部门/分类（一二级）/仓库/供应商/用户管理、**角色管理（可视化权限勾选配置）**、**折旧配置（按分类自定义折旧算法+残值率）**、操作日志（日期范围+关键字筛选）

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
python3 main.py
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
cd ../backend && pip install -r requirements.txt && python3 main.py
```

访问 `http://localhost:8000`，前端已内嵌到后端服务。

## 关闭

- **开发模式** — 分别在两个终端按 `Ctrl+C` 停止前后端
- **生产模式** — 在终端按 `Ctrl+C` 停止后端服务
- 数据保存在 `backend/data/it_assets.db`，关闭不会丢失

## 角色权限（RBAC 3.0）

系统采用「用户 → 角色 → 权限码」三层 RBAC 模型，支持超级管理员自由创建/编辑角色并勾选权限，实现灵活的人员权限分配。

### 权限码体系（38 个，10 模块）

| 模块 | 权限码 |
|------|--------|
| 仪表盘 | `dashboard:view` |
| 资产管理 | `asset:read` `asset:create` `asset:update` `asset:delete` `asset:import` `asset:export` |
| 库存管理 | `stock:query` `stock:in` `stock:out` `stock:return` `stock:transfer` `stock:check` `stock:warning` |
| 维保管理 | `repair:read` `repair:create` `repair:update` `repair:return` |
| 报废管理 | `scrap:read` `scrap:create` |
| 审批流 | `approval:submit` `approval:approve` `approval:deliver` |
| 报表统计 | `report:summary` `report:stock` `report:inout` `report:depreciation` |
| 系统管理 | `system:user` `system:role` `system:dept` `system:category` `system:warehouse` `system:supplier` `system:log` `system:dict` |
| 折旧 | `depreciation:config` `depreciation:calculate` |
| 通知 | `notification:view` |

### 数据范围（scope）

| 范围 | 说明 |
|------|------|
| `all` | 全量数据，无限制 |
| `dept` | 仅本部门数据 |
| `self` | 仅本人数据 |

### 内置角色

| 角色 | scope | 关键权限 |
|------|-------|---------|
| 超级管理员 | all | 全部 38 个权限 |
| 资产管理员 | all | 业务操作完整权限，不含系统管理 |
| 部门主管 | dept | 查看 + 审批本部门数据 |
| 普通用户 | self | 查看资产 + 提交审批 |
| 审计员 | all | 全部只读权限（无增删改） |

## 项目结构

```
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── database.py           # 数据库初始化与连接
│   ├── auth.py               # JWT 认证 + require_permission 权限依赖 + scope 数据隔离
│   ├── schemas.py            # Pydantic 数据模型
│   ├── requirements.txt
│   └── routers/              # API 路由（11 个模块）
│       ├── auth.py           # 登录/登出
│       ├── assets.py         # 资产 CRUD + 导入导出 + 时间线 + 折旧计算 + 保修预警
│       ├── stock.py          # 出入库/库存/预警 + 盘点确认
│       ├── repairs.py        # 维修记录 + 返修入库
│       ├── scraps.py         # 报废管理（独立模块）
│       ├── approvals.py      # 领用审批流（申请→审批→出库）+ scope 数据隔离
│       ├── roles.py          # 角色 CRUD + 权限码列表
│       ├── notifications.py  # 通知中心
│       ├── reports.py        # 报表统计（含折旧报表）
│       ├── system.py         # 部门/分类/仓库/供应商/用户/日志管理
│       └── depreciation.py   # 折旧配置管理
└── frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── api/index.js      # Axios 封装
        ├── router/index.js   # 路由配置
        ├── components/       # 公共组件（含 NotificationBell）
        └── views/            # 页面组件（25 个页面，含角色管理）
```

## 文档

- [用户操作手册](USER-MANUAL.md)
- [迭代变更日志](CHANGELOG.md)
- [产品需求文档](PRD-3.0.md)
- [API 接口契约](API-CONTRACT.md)
- [测试报告](TEST-REPORT.md)

## 环境要求

- Python 3.9+
- Node.js 18+

## 安全

- JWT 密钥通过环境变量 `IT_ASSET_SECRET` 配置
- 密码 bcrypt 哈希存储，参数化查询防 SQL 注入
- 操作权限后端逐端点校验（`require_permission` 依赖注入，44 项自动化测试覆盖）
- 角色权限码白名单校验，内置角色不可修改/删除
- JWT 不缓存权限，权限变更即时生效

## License

MIT
