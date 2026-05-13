# IT 资产管理系统

轻量化、安全可控的本地 IT 资产进销存管理系统。基于 **Vue3 + Element Plus** 前端与 **FastAPI + SQLite** 后端，单文件数据库即装即用，适合中小企业 IT 资产的全生命周期管理。

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端框架 | Vue 3 (Composition API) | `<script setup>` 语法 |
| UI 组件库 | Element Plus | 中文 locale，暗色侧边栏 |
| 图表 | ECharts (vue-echarts) | 仪表盘统计图表 |
| 路由 | Vue Router 4 | Hash 模式，登录鉴权守卫 |
| 后端框架 | FastAPI | Python 异步 Web 框架 |
| 数据库 | SQLite | WAL 模式，文件存储 |
| 认证 | JWT + bcrypt | HS256，24 小时有效期 |
| 数据校验 | Pydantic v2 | Field 约束（min_length、ge、gt） |

## 功能模块

### 仪表盘
- 6 个统计卡片（资产总数/在库/使用中/维修中/借出/已报废）
- ECharts 柱状图（资产状态分布）+ 环形图（分类占比）
- 最近操作日志 + 库存预警提醒

### 资产管理
- **资产列表**：多条件查询、分页、二维码弹窗
- **资产登记**：自动生成编号 `IT-YYYYMM-NNNN`，关联分类/部门/仓库/供应商
- **资产盘点**：按仓库/分类筛选，批量标记盘点状态
- **Excel 导入导出**：批量导入资产，导出资产清单

### 库存管理
- **库存查询**：多维筛选 + 行内快捷操作（入库/出库/归还/报废）
- **入库管理**：采购入库、借调入库，支持远程搜索资产
- **出库管理**：领用出库、借用出库，自动更新资产状态

### 维保管理
- **维修记录**：新增/编辑/完成维修，自动关联资产状态
- **报废管理**：确认报废并记录，不可撤销

### 报表统计
- **资产汇总**：按状态统计数量与总价值
- **库存统计**：按分类/状态/部门三维分析
- **出入库报表**：按日期和类型筛选明细

### 系统管理
- 部门管理、分类管理、供应商管理、仓库管理
- 库存预警规则（最低/最高库存阈值）
- 操作日志（只读）
- 用户管理（管理员专属：新增/编辑/删除/重置密码）

## 项目结构

```
it资产管理/
├── backend/
│   ├── main.py              # FastAPI 入口，CORS，静态文件挂载
│   ├── database.py           # SQLite 初始化，9张表，种子数据
│   ├── auth.py               # JWT 签发/验证，bcrypt 密码哈希
│   ├── schemas.py            # Pydantic 请求/响应模型，数据校验
│   ├── requirements.txt      # Python 依赖
│   └── routers/
│       ├── auth.py           # 登录/登出/当前用户
│       ├── assets.py         # 资产 CRUD + 二维码 + 导入导出
│       ├── stock.py          # 出入库/归还/调拨/库存查询/预警
│       ├── repairs.py        # 维修记录 + 报废
│       ├── reports.py        # 资产汇总/库存统计/出入库报表
│       └── system.py         # 部门/分类/供应商/仓库/预警/日志/用户
└── frontend/
    ├── package.json          # 依赖声明
    ├── vite.config.js        # Vite 配置，API 代理
    ├── index.html            # 入口 HTML
    └── src/
        ├── main.js           # Vue 应用启动，Element Plus 注册
        ├── App.vue           # 根组件，CSS 变量，过渡动画
        ├── api/index.js      # Axios 实例，拦截器
        ├── router/index.js   # 路由配置，登录守卫
        ├── components/
        │   └── Layout.vue    # 可折叠侧边栏 + 面包屑 + 用户菜单
        └── views/
            ├── Login.vue     # 登录页（左品牌 + 右表单）
            ├── Dashboard.vue # 仪表盘
            ├── assets/       # AssetList, AssetForm, CheckPlan
            ├── stock/        # StockQuery, StockIn, StockOut
            ├── repairs/      # RepairList, ScrapList
            ├── reports/      # StockReport, InoutReport, SummaryReport
            └── system/       # 7 个管理页面 + Users
```

## 快速开始

### 环境要求
- Python 3.9+
- Node.js 18+

### 1. 启动后端

```bash
cd backend
pip install -r requirements.txt
python main.py
# 后端运行在 http://localhost:8000
# API 文档：http://localhost:8000/docs
```

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
# 前端运行在 http://localhost:5173
# 已配置代理将 /api 转发到后端
```

### 3. 登录系统

- 地址：`http://localhost:5173`
- 默认账号：`admin` / `admin123`

### 生产部署

```bash
# 构建前端
cd frontend && npm run build

# 启动后端（自动挂载前端静态文件）
cd ../backend && python main.py
# 访问 http://localhost:8000 即可
```

## 数据库

- 位置：`backend/data/it_assets.db`
- 单文件 SQLite，WAL 模式，支持并发读写
- 首次启动自动建表并插入种子数据（管理员账号、默认分类/部门/仓库）
- 共 9 张表：users、departments、categories、warehouses、suppliers、assets、stock_records、repairs、stock_warnings、operation_logs

## 安全说明

- JWT 密钥通过环境变量 `IT_ASSET_SECRET` 配置，未设置时随机生成（每次重启变化）
- 密码使用 bcrypt 哈希存储
- 所有接口使用参数化查询，防止 SQL 注入
- Pydantic 模型对输入参数进行长度/范围校验
- CORS 允许来源通过 `ALLOWED_ORIGINS` 环境变量配置
- 管理员专属操作（用户管理、删除资产）后端二次校验角色

## License

MIT
