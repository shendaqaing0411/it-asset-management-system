# IT 资产管理系统 — 迭代变更日志

---

## 版本 3.0.2（2026-05-18）

### Bug 修复
- 修复所有导出按钮 404 错误：`downloadCsv` 调用方移除冗余 `/api` 前缀，axios 实例已自带 `baseURL: '/api'`
- 修复资产 CSV 导出状态字段显示英文（in_stock/borrowed...）→ 中文（在库/借出...）
- 修复维修记录 CSV 导出维修状态显示英文 → 中文
- 修复折旧报表 CSV 导出折旧方法显示英文（straight/once）→ 中文（直线法/一次性）
- 修复折旧计算逻辑 bug：无使用年限时净值未扣减累计折旧（`net = price` → `net = max(price - accumulated, 0)`）
- 修复折旧配置新增/删除的边界校验：非法 method/负数年限/负数残值率/不存在分类ID/删除不存在配置

### 新增
- 资产列表表格新增「备注」列展示
- 库存查询表格新增「备注」列展示
- 折旧报表新增「分类」列和按分类汇总表
- 折旧配置管理模块（系统管理 → 折旧配置）：按资产分类自定义折旧方法、使用年限、残值率
- 折旧计算逻辑增强：优先读取分类折旧配置，支持残值率参数

### 改进
- 折旧报表 CSV 导出增加分类列、月折旧额列、底部分类汇总区域
- 折旧配置 Pydantic 模型增加 Field 约束（`gt=0`, `ge=0`, `le=1`, `Literal["straight","once"]`）

---

## 版本 3.0（2026-05-18）

### 概述

3.0 是一次架构升级版本，引入了角色权限体系重构、领用审批工作流、通知中心、资产折旧管理、资产时间线等 5 个全新模块，并对维修流程、报废管理、盘点功能、CSV 导出等既有模块进行了深度增强。

### 新增模块

#### 1. 角色权限体系重构

| 变更项 | 1.0/2.0 | 3.0 |
|--------|---------|-----|
| 角色数 | 2（admin / user） | 5（super_admin / asset_admin / dept_manager / user / auditor） |
| 权限校验 | 内联 `if user["role"] != "admin"` | 统一 `require_role(*roles)` 依赖注入 |
| admin 角色 | `admin` | 重命名为 `super_admin` |
| 新增角色 | — | `asset_admin`（资产管理员）、`dept_manager`（部门主管）、`auditor`（审计员） |

**影响范围**: 所有系统管理模块的写入操作均改用 `require_role("super_admin", "asset_admin")` 校验。

#### 2. 领用审批工作流

**新增文件**: `backend/routers/approvals.py`（156行）、`frontend/src/views/stock/ApprovalList.vue`（158行）

**新增数据库表**: `approvals`（id, asset_id, applicant_id, approver_id, dept_id, status, apply_reason, reject_reason, apply_date, approve_date, deliver_date, create_time）

**状态机**:
```
提交申请 → 待审批(pending)
              ↓ 通过           ↓ 拒绝
          已通过(approved)   已拒绝(rejected)
              ↓ 确认出库
          已出库(delivered)
```

**新增 API**:

| 方法 | 路径 | 功能 | 权限 |
|------|------|------|------|
| GET | `/api/approvals` | 查询审批列表（按角色过滤） | 登录用户 |
| POST | `/api/approvals` | 提交领用申请 | user / dept_manager |
| PUT | `/api/approvals/{id}/approve` | 审批通过/拒绝 | super_admin / asset_admin / dept_manager |
| PUT | `/api/approvals/{id}/deliver` | 确认出库 | super_admin / asset_admin |

**前端功能**:
- 三 Tab 切换：我的申请 / 待审批 / 待出库
- 远程搜索资产下拉框
- 拒绝原因弹窗
- 状态标签颜色编码（pending=warning, approved=success, rejected=danger, delivered=info）
- CSV 导出

#### 3. 通知中心

**新增文件**: `backend/routers/notifications.py`（57行）、`frontend/src/components/NotificationBell.vue`（114行）

**新增数据库表**: `notifications`（id, user_id, type, title, content, is_read, ref_id, create_time）

**新增 API**:

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/notifications` | 分页查询通知列表（支持 ?unread 过滤） |
| GET | `/api/notifications/count` | 获取未读通知数量 |
| PUT | `/api/notifications/{id}/read` | 标记单条通知已读 |

**通知触发场景**:

| 类型 | 触发时机 |
|------|----------|
| `approval_pending` | 用户提交领用申请 → 通知所有管理员 |
| `approval_pending` | 审批完成 → 通知申请人 |
| `repair_complete` | 维修状态变更为完成 → 通知管理员 |
| `warranty_expire` | 系统检测到保修即将到期 |
| `stock_low` | 库存低于预警阈值 |

**前端组件**:
- 顶部栏铃铛图标，30 秒轮询未读数
- 有未读消息时铃铛抖动动画
- 点击通知自动标记已读并跳转到相关页面

#### 4. 资产折旧管理

**新增文件**: `frontend/src/views/reports/Depreciation.vue`（98行）

**assets 表新增列**:
| 列名 | 类型 | 说明 |
|------|------|------|
| `purchase_lifespan_years` | INTEGER | 使用年限（年） |
| `depreciation_method` | VARCHAR(20) | 折旧方法：straight（直线法）/ once（一次性） |
| `monthly_depreciation` | DECIMAL(12,2) | 月折旧额 |
| `accumulated_depreciation` | DECIMAL(12,2) | 累计折旧 |
| `net_value` | DECIMAL(12,2) | 净值 |

**新增 API**:

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/assets/calculate-depreciation` | 批量计算所有在库/使用中资产的折旧 |
| GET | `/api/report/depreciation` | 折旧报表（含汇总统计），支持 CSV 导出 |

**前端功能**:
- 汇总卡片：原值总额 / 累计折旧 / 净值总额
- 折旧方法标签：直线法 / 一次性
- 折旧状态标签：折旧中 / 已折旧 / 未折旧
- 一键执行折旧计算

#### 5. 资产时间线

**新增文件**: `frontend/src/views/assets/AssetTimeline.vue`（68行）

**新增 API**: `GET /api/assets/{id}/timeline`

**数据来源**: UNION ALL 查询 stock_records + repairs + scraps 三表

**时间线事件**:

| 事件 | 颜色 | Element Plus 图标 |
|------|------|-------------------|
| 入库 | #34c88d（绿） | Box |
| 出库 | #5b7cfa（蓝） | Upload |
| 维修 | #f5a623（橙） | Tools |
| 返修入库 | #34c88d（绿） | Download |
| 报废 | #f55858（红） | Delete |

---

### 增强模块

#### 6. 报废管理独立化

**变更**: 报废功能从 `repairs.py` 路由中分离，创建独立的 `scraps.py` 路由。

**新增文件**: `backend/routers/scraps.py`（61行）

**新增数据库表**: `scraps`（id, asset_id, scrap_reason, aging_match, damage_responsible, scrap_date, remark, operator_id, create_time）

**报废原因枚举**:

| 原因 | 必填验证 |
|------|----------|
| 自然老化 | 必须确认 aging_match = true（与资产使用年限匹配） |
| 人为损坏 | 必须填写 damage_responsible（责任人） |

**前端改造（ScrapList.vue）**:
- 报废原因改为 `el-radio` 单选
- 自然老化：显示年限匹配确认开关
- 人为损坏：显示责任人输入框
- 新增报废日期选择器

#### 7. 维修流程增强

**repairs 表新增列**: `repair_method`（维修方式）、`return_date`（返修日期）、`return_confirmed`（返修确认标记）

**维修类型枚举化**:
`POST /api/repairs` 的 `repair_type` 字段限制为 4 个可选值：
- 保修期内维修
- 保外维修
- 厂商送修
- 自行维修

**关键流程变更**: 维修完成 ≠ 自动入库

| 2.0 | 3.0 |
|-----|-----|
| 维修状态设为 finished → 资产自动恢复 in_stock | 维修完成 → 通知管理员 → 手动点击「返修入库」→ 资产恢复 in_stock |

**新增 API**: `POST /api/repairs/{id}/return`

#### 8. 盘点确认

**新增 API**: `POST /api/stock/check`

**新增 Schema**: `CheckItem`（asset_id, result, remark）、`CheckReq`（items: list）

**盘点结果**:
- normal：正常
- surplus：盘盈 → 自动生成盘盈入库记录
- loss：盘亏 → 自动生成盘亏出库记录

**前端**: CheckPlan.vue 新增批量盘点功能，支持逐项标记盘盈/盘亏/正常。

#### 9. 入库/出库类型扩展

| 模块 | 新增选项 |
|------|----------|
| 入库管理（StockIn.vue） | 盘盈入库 |
| 出库管理（StockOut.vue） | 盘亏出库 |

#### 10. 保修期预警

**新增 API**: `GET /api/assets/warranty-alerts?days=30`

**前端**: Dashboard.vue 新增保修预警卡片，显示未来 N 天内保修到期的资产。

#### 11. CSV 导出增强

| 页面 | 导出入口 |
|------|----------|
| 资产列表 | 「导出 Excel」按钮 |
| 领用审批 — 我的申请 | 「导出」按钮 |
| 折旧报表 | 「导出」按钮 |
| 后端通用 | `GET /api/assets?format=csv`、`GET /api/report/depreciation?format=csv`、`GET /api/approvals?format=csv` |

---

### 代码结构变更

**新增后端文件**: 3 个
```
backend/routers/scraps.py         61 行
backend/routers/approvals.py     156 行
backend/routers/notifications.py  57 行
```

**新增前端文件**: 4 个
```
frontend/src/views/assets/AssetTimeline.vue    68 行
frontend/src/views/stock/ApprovalList.vue      158 行
frontend/src/views/reports/Depreciation.vue     98 行
frontend/src/components/NotificationBell.vue   114 行
```

**修改后端文件**: 9 个（auth.py、database.py、schemas.py、main.py、assets.py、stock.py、repairs.py、reports.py、system.py）

**修改前端文件**: 9 个（Layout.vue、router/index.js、Dashboard.vue、AssetList.vue、CheckPlan.vue、ScrapList.vue、RepairList.vue、StockIn.vue、StockOut.vue）

**API 端点**: 60 → 73（净增 13 个）

**数据库**: 新增 3 张表 + 8 列迁移

**新增 Pydantic Schema**: ScrapCreate、ApprovalCreate、ApprovalApprove、RepairReturnReq、CheckItem、CheckReq

---

## 版本 2.0（2026-05-14 ~ 2026-05-17）

### 概述

2.0 在 1.0 基础上新增了数据字典、二级分类、批量导入等模块，并对操作日志和报表进行了增强。

### 新增模块

#### 1. 数据字典

**新增文件**: `backend/routers/dict.py`（147行）

**功能**: 字段定义表 + 字典值表两级管理，支持系统中可配置的下拉选项动态维护。

**API**:
- 字段定义 CRUD: `GET/POST /api/dict/fields`、`PUT/DELETE /api/dict/fields/{field_id}`
- 字典值管理: `GET/POST /api/dict/values`

**前端**: `frontend/src/views/system/Dict.vue`

#### 2. 二级分类体系

**变更**: categories 表新增 `parent_id` 字段，实现分类层级。

**业务规则**: 资产只能挂载到二级分类下（`parent_id != 0`）。

#### 3. 资产批量导入

**新增 API**:
- `GET /api/assets/import/template` — Excel 模板下载
- `POST /api/assets/import` — 批量导入

**前端**: 三步导入向导（下载模板 → 上传文件 → 预览确认 → 执行导入）

#### 4. 操作日志增强

**变更**: `/api/logs` 接口新增日期范围筛选（`start_date`/`end_date`）和关键字搜索（`keyword`）参数。

### 修改内容

| 文件 | 变更 |
|------|------|
| `backend/routers/system.py` | +113 行，新增 dict 相关支持 |
| `backend/routers/assets.py` | +31 行，新增 import/export 端点 |
| `backend/routers/reports.py` | +37 行，报表增强 |
| `backend/routers/stock.py` | +7 行 |

**总计**: 73 文件变更，+1686 行，-321 行

---

## 版本 1.0（2026-05-13）

### 概述

IT 资产管理系统的初始全栈实现，建立了基础架构和核心业务模块。

### 初始架构

**后端**: FastAPI + SQLite + JWT 认证
**前端**: Vue 3 + Element Plus + ECharts
**认证**: bcrypt 密码哈希 + JWT HS256（24h 过期）

### 初始模块

| 模块 | Router | 端点 | 说明 |
|------|--------|------|------|
| 认证 | auth.py | 3 | 登录/登出/当前用户 |
| 资产管理 | assets.py | 10 | CRUD + 二维码 + 导出 |
| 库存管理 | stock.py | 7 | 出入库/调拨/归还/记录/预警 |
| 维修管理 | repairs.py | 5 | 维修记录 CRUD + 报废（耦合在维修模块） |
| 报表统计 | reports.py | 3 | 资产汇总/库存统计/出入库报表 |
| 系统管理 | system.py | 25 | 部门/分类/供应商/仓库/预警/日志/用户 CRUD |

### 初始数据库表

assets、stock_records、repairs、departments、categories、suppliers、warehouses、warnings、operation_logs、users

### 初始前端页面

仪表盘、资产列表、资产登记、资产盘点、库存查询、入库管理、出库管理、维修记录（含报废）、库存统计、出入库报表、资产汇总、部门管理、分类管理、供应商管理、仓库管理、库存预警、操作日志、用户管理、登录页

---

## 版本对比总览

| | 1.0 | 2.0 | 3.0 |
|---|---|---|---|
| **发布日期** | 2026-05-13 | 2026-05-17 | 2026-05-18 |
| **API 端点** | ~55 | 60 | 73 |
| **后端 Router** | 6 | 7 | 10 |
| **数据库表** | 10 | 12 | 15 |
| **前端页面** | 19 | 20 | 24 |
| **前端组件** | 基础 | 基础 | +NotificationBell |
| **角色数** | 2 | 2 | 5 |
| **审批工作流** | ❌ | ❌ | ✅ |
| **通知中心** | ❌ | ❌ | ✅ |
| **折旧管理** | ❌ | ❌ | ✅ |
| **资产时间线** | ❌ | ❌ | ✅ |
| **数据字典** | ❌ | ✅ | ✅ |
| **二级分类** | ❌ | ✅ | ✅ |
| **批量导入** | ❌ | ✅ | ✅ |
| **保修预警** | ❌ | ❌ | ✅ |
| **盘点确认** | 基础 | 基础 | 增强（盘盈/盘亏联动） |
| **报废管理** | 耦合在维修 | 耦合在维修 | 独立模块（原因分类校验） |
| **CSV 导出** | 资产列表 | 资产列表 | 3 处入口 |
