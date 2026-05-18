# IT 资产管理系统 3.0 产品需求文档

> 版本：3.0 | 日期：2026-05-18 | 状态：待评审
>
> 基于 Vue3 + FastAPI + SQLite 的本地 IT 资产管理系统，在原 2.x 基础上增加角色权限体系、资产全生命周期时间线、维保模块重构、库存类型扩展、审批流、折旧计算、保修提醒、通知中心、数据导出、资产盘点联动十大改造模块。

---

## 目录

1. [角色权限体系](#1-角色权限体系)
2. [资产全生命周期时间线](#2-资产全生命周期时间线)
3. [维保模块重构](#3-维保模块重构)
4. [库存类型扩展](#4-库存类型扩展)
5. [资产领用审批流](#5-资产领用审批流)
6. [折旧计算](#6-折旧计算)
7. [保修到期提醒](#7-保修到期提醒)
8. [通知中心](#8-通知中心)
9. [数据导出](#9-数据导出)
10. [资产盘点联动](#10-资产盘点联动)

---

## 1. 角色权限体系

### 1.1 角色定义

系统内置 5 种角色，不可删除、不可更名：

| 角色 | 标识 | 说明 |
|---|---|---|
| 超级管理员 | `admin` | 系统全局管理，唯一内置管理员账号不可删除 |
| 资产管理员 | `asset_manager` | 负责资产录入、出入库、维保报废操作 |
| 部门主管 | `dept_manager` | 审批本部门资产领用申请、查看本部门资产 |
| 普通用户 | `user` | 申请领用资产、查看个人持有资产 |
| 审计员 | `auditor` | 只读查看所有数据、操作日志，无任何写权限 |

### 1.2 权限矩阵

权限动作代码约定：`C` = 创建 / `R` = 读取 / `U` = 更新 / `D` = 删除 / `A` = 审批

| 模块 | 权限项 | 超级管理员 | 资产管理员 | 部门主管 | 普通用户 | 审计员 |
|---|---|---|---|---|---|---|
| **仪表盘** | 查看全局统计 | R | R | 仅本部门 | 仅本人 | R |
| **资产管理** | 查看资产列表 | R | R | 仅本部门 | 仅本人 | R |
| | 登记/编辑资产 | C,U | C,U | - | - | - |
| | 删除资产 | D | - | - | - | - |
| | 导入资产 | C | C | - | - | - |
| | 导出资产 | C | C | 仅本部门 | - | C |
| **库存管理** | 入库 | C | C | - | - | - |
| | 出库（领用/借用） | C | C | - | - | - |
| | 归还 | C | C | - | - | - |
| | 调拨 | C | C | - | - | - |
| | 库存查询 | R | R | 仅本部门 | - | R |
| | 库存预警设置 | C,U | C,U | - | - | - |
| **维保管理** | 维修登记/编辑 | C,U | C,U | - | - | - |
| | 返修入库确认 | C | C | - | - | - |
| | 报废登记 | C,U | C,U | - | - | - |
| | 维保记录查看 | R | R | 仅本部门 | - | R |
| **审批流** | 提交领用申请 | C | C | C | C | - |
| | 审批申请 | - | - | A（本部门）| - | - |
| | 确认出库 | C | C | - | - | - |
| **报表统计** | 资产汇总 | R | R | 仅本部门 | - | R |
| | 库存统计 | R | R | 仅本部门 | - | R |
| | 出入库报表 | R | R | 仅本部门 | - | R |
| | 折旧报表 | R | R | 仅本部门 | - | R |
| **系统管理** | 部门管理 | C,U,D | - | - | - | R |
| | 分类管理 | C,U,D | - | - | - | R |
| | 仓库管理 | C,U,D | - | - | - | R |
| | 供应商管理 | C,U,D | - | - | - | R |
| | 用户管理 | C,U,D | - | - | - | R |
| | 操作日志 | R | - | - | - | R |
| | 数据字典 | C,U,D | - | - | - | R |
| **通知中心** | 查看通知 | R | R | R | R | R |
| | 标记已读 | U | U | U | U | U |
| **盘点** | 执行盘点 | C | C | - | - | - |
| | 查看盘点结果 | R | R | 仅本部门 | - | R |

### 1.3 后端权限装饰器设计

FastAPI 依赖注入方式实现，不引入额外框架。

```text
# 权限控制伪代码（不实现，仅描述设计）

def require_role(*roles: str):
    """角色检查依赖：
    Depends(require_role("admin", "asset_manager"))
    传入允许的角色列表，不在列表内返回 403
    """

def require_dept_scope():
    """部门数据范围依赖：
    部门主管自动过滤 dept_id = 本人的部门
    普通用户自动过滤 user_id = 本人
    admin/asset_manager/auditor 不做过滤
    """

def require_any_role(*roles: str):
    """满足任一角色即可，同 require_role"""
```

**使用示例：**
- `POST /api/assets` → `Depends(require_role("admin", "asset_manager"))`
- `GET /api/assets` → `Depends(require_role("admin", "asset_manager", "auditor")), Depends(require_dept_scope())`
- `DELETE /api/assets/{id}` → `Depends(require_role("admin"))`
- `POST /api/approvals/{id}/approve` → `Depends(require_role("admin", "dept_manager"))`

### 1.4 users 表变更

在现有 `users` 表基础上，`role` 字段扩展为枚举：

```sql
-- role 字段值约束（代码层强制，SQLite 无原生 ENUM）
-- 合法值：'admin' | 'asset_manager' | 'dept_manager' | 'user' | 'auditor'

ALTER TABLE users ADD COLUMN dept_id INTEGER DEFAULT NULL REFERENCES departments(id);
```

`dept_id` 字段用于部门主管绑定其所管辖的部门，审批时校验申请人是否属于同一部门。

---

## 2. 资产全生命周期时间线

### 2.1 接口定义

**GET /api/assets/{id}/timeline**

查询参数：无

响应：
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "asset": {
      "id": 1,
      "asset_no": "IT-202601-0001",
      "name": "ThinkPad X1 Carbon",
      "status": "in_use"
    },
    "timeline": [
      {
        "id": 1,
        "event_type": "stock_in",
        "event_label": "采购入库",
        "operator_name": "管理员",
        "occurred_at": "2026-01-15 10:30:00",
        "detail": {
          "type": "采购入库",
          "warehouse": "主仓库",
          "remark": "年度采购"
        }
      },
      {
        "id": 2,
        "event_type": "stock_out",
        "event_label": "领用出库",
        "operator_name": "张三",
        "occurred_at": "2026-01-20 14:00:00",
        "detail": {
          "type": "领用出库",
          "dept": "技术部",
          "user": "李四"
        }
      },
      {
        "id": 3,
        "event_type": "repair",
        "event_label": "报修",
        "operator_name": "李四",
        "occurred_at": "2026-02-10 09:00:00",
        "detail": {
          "fault_desc": "屏幕闪烁",
          "repair_type": "保修期内维修",
          "status": "finished"
        }
      },
      {
        "id": 4,
        "event_type": "transfer",
        "event_label": "调拨",
        "operator_name": "管理员",
        "occurred_at": "2026-03-01 11:00:00",
        "detail": {
          "from_warehouse": "主仓库",
          "to_warehouse": "备件库"
        }
      },
      {
        "id": 5,
        "event_type": "scrap",
        "event_label": "报废",
        "operator_name": "资产管理员",
        "occurred_at": "2026-04-01 16:00:00",
        "detail": {
          "scrap_reason": "自然老化",
          "aging_match": true
        }
      }
    ]
  }
}
```

### 2.2 event_type 枚举

| event_type | event_label | 数据来源表 |
|---|---|---|
| `stock_in` | 入库 | stock_records |
| `stock_out` | 出库 | stock_records |
| `return` | 归还 | stock_records |
| `transfer` | 调拨 | stock_records |
| `repair` | 维修 | repairs |
| `repair_return` | 返修入库 | repairs |
| `scrap` | 报废 | scraps |
| `check_in` | 盘盈入库 | stock_records |
| `check_out` | 盘亏出库 | stock_records |
| `create` | 资产登记 | assets（首次登记，取 create_time） |

### 2.3 后端实现逻辑

后端从三张表联合查询：`stock_records`、`repairs`、`scraps`（新增报废表），加上资产本身的 `create_time` 作为「资产登记」事件，按 `occurred_at` 升序排列。每条记录附带操作人姓名（JOIN users）。

### 2.4 前端展示

- 左侧竖向时间线（Element Plus Timeline 组件），从最早到最新。
- 每条时间线节点显示：图标（区分事件类型）、事件标签、操作人、时间、详情浮层。
- 图标映射：入库（el-icon-box）、出库（el-icon-sell）、归还（el-icon-refresh-left）、调拨（el-icon-right）、维修（el-icon-setting）、报废（el-icon-delete）。

---

## 3. 维保模块重构

### 3.1 菜单结构变更

原「维保报废」拆分为「维保管理」主菜单，内含两个子菜单：

```
维保管理
  ├── 维修记录
  └── 报废记录
```

### 3.2 维修增强

#### 3.2.1 repairs 表变更

```sql
-- 在现有 repairs 表上扩展
ALTER TABLE repairs ADD COLUMN repair_method VARCHAR(20) DEFAULT '';  -- 维修方式
ALTER TABLE repairs ADD COLUMN return_date DATE;                       -- 返修入库日期
ALTER TABLE repairs ADD COLUMN return_operator_id INTEGER;             -- 确认入库操作人
```

完整字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 自增主键 |
| asset_id | INTEGER FK | 资产ID |
| fault_desc | VARCHAR(500) | 故障描述 |
| repair_type | VARCHAR(20) | 维修类型（枚举） |
| repair_method | VARCHAR(20) | 维修方式（枚举） |
| repair_cost | DECIMAL(10,2) | 维修费用 |
| repair_date | DATE | 报修日期 |
| finish_date | DATE | 维修完成日期 |
| return_date | DATE | 返修入库确认日期 |
| return_operator_id | INTEGER | 入库确认操作人 |
| status | VARCHAR(20) | 状态：`pending` / `repairing` / `finished` / `returned` |
| operator_id | INTEGER | 登记人 |
| remark | VARCHAR(500) | 备注 |
| create_time | DATETIME | 创建时间 |

#### 3.2.2 repair_type 枚举

| 值 | 含义 |
|---|---|
| `in_warranty` | 保修期内维修 |
| `out_warranty` | 保外维修 |
| `vendor_repair` | 厂商送修 |
| `self_repair` | 自行维修 |

#### 3.2.3 repair_method 枚举

| 值 | 含义 |
|---|---|
| `replace_parts` | 更换配件 |
| `software_fix` | 软件修复 |
| `cleaning` | 清洁保养 |
| `factory_return` | 返厂维修 |

#### 3.2.4 状态流转

```
pending ──维修中──> repairing ──维修完成──> finished ──返修确认入库──> returned
```

- `pending`：报修登记，资产状态保持原样（仍为 in_use / in_stock）
- `repairing`：开始维修，资产状态变为 `repairing`
- `finished`：维修完成，资产状态仍为 `repairing`（等待入库确认）
- `returned`：入库确认，资产状态变为 `in_stock`

#### 3.2.5 API 变更

**POST /api/repairs** — 创建维修记录（保持不变，新增字段）

Request body：
```json
{
  "asset_id": 1,
  "fault_desc": "屏幕闪烁，无法正常显示",
  "repair_type": "in_warranty",
  "repair_method": "replace_parts",
  "repair_cost": 500.00,
  "repair_date": "2026-05-01"
}
```

Response：
```json
{
  "code": 0,
  "message": "维修记录已创建",
  "data": { "id": 1 }
}
```

**PUT /api/repairs/{id}** — 更新维修记录（保持不变，扩展可更新字段）

Request body：
```json
{
  "status": "finished",
  "finish_date": "2026-05-07",
  "repair_cost": 500.00,
  "remark": "已更换屏幕面板"
}
```

**POST /api/repairs/{id}/return** — 返修入库确认（新增接口）

Request body：
```json
{}
```

业务逻辑：
1. 校验维修记录 status == `finished`
2. 将 `return_date` 设为当前日期，`return_operator_id` 设为当前用户
3. 将 repairs.status 更新为 `returned`
4. 将对应资产的 status 更新为 `in_stock`

Response：
```json
{
  "code": 0,
  "message": "返修入库确认完成"
}
```

### 3.3 报废增强

#### 3.3.1 scraps 表（新建，不再复用 stock_records）

```sql
CREATE TABLE IF NOT EXISTS scraps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL REFERENCES assets(id),
    scrap_reason VARCHAR(20) NOT NULL,       -- 报废原因：natural_aging / human_damage
    aging_match INTEGER DEFAULT 1,           -- 是否匹配使用年限：1=匹配 / 0=不匹配
    damage_responsible VARCHAR(50),          -- 人为损坏责任人（human_damage 时必填）
    scrap_date DATE NOT NULL,                -- 报废日期
    operator_id INTEGER,                     -- 操作人
    remark VARCHAR(500),                     -- 备注
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 自增主键 |
| asset_id | INTEGER FK | 资产ID |
| scrap_reason | VARCHAR(20) | 报废原因：`natural_aging`（自然老化）/ `human_damage`（人为损坏） |
| aging_match | INTEGER | 是否匹配使用年限：1=匹配 / 0=不匹配（仅 natural_aging 时生效） |
| damage_responsible | VARCHAR(50) | 人为损坏责任人（human_damage 时必填） |
| scrap_date | DATE | 报废日期 |
| operator_id | INTEGER | 操作人ID |
| remark | VARCHAR(500) | 备注说明 |
| create_time | DATETIME | 创建时间 |

#### 3.3.2 报废业务校验

**自然老化（natural_aging）校验逻辑：**

1. 获取资产 `purchase_date` 和 `purchase_lifespan_years`
2. 如果 `purchase_lifespan_years > 0`：
   - 计算实际使用年限 = `scrap_date - purchase_date`（年）
   - 如果实际使用年限 >= `purchase_lifespan_years × 0.8` → `aging_match = true`
   - 否则 → `aging_match = false`，前端给出警告提示「该资产实际使用年限不足采购年限的 80%，请确认是否提前报废」
3. 如果 `purchase_lifespan_years == 0`：
   - `aging_match` 字段前端不显示，后端默认 null

**人为损坏（human_damage）校验：**
- `damage_responsible` 字段必填，不可为空字符串

#### 3.3.3 API 变更

**GET /api/scraps** — 报废列表（独立数据源）

查询参数：`?page=1&page_size=20&asset_id=`

响应：
```json
{
  "code": 0,
  "data": {
    "total": 50,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "asset_id": 10,
        "asset_no": "IT-202501-0010",
        "asset_name": "Dell 显示器",
        "scrap_reason": "natural_aging",
        "aging_match": 1,
        "damage_responsible": null,
        "scrap_date": "2026-05-01",
        "operator_name": "管理员",
        "remark": "屏幕老化严重",
        "create_time": "2026-05-01 10:00:00"
      }
    ]
  }
}
```

**POST /api/scraps** — 报废登记（替换旧接口）

Request body：
```json
{
  "asset_id": 10,
  "scrap_reason": "natural_aging",
  "aging_match": 1,
  "damage_responsible": null,
  "scrap_date": "2026-05-01",
  "remark": "屏幕老化严重，达到使用年限"
}
```

Response：
```json
{
  "code": 0,
  "message": "报废登记完成",
  "data": { "id": 1, "aging_warning": false }
}
```

`aging_warning` 字段：当前端提交 `aging_match = 0` 时返回 `true`，提醒用户已知悉。

**DELETE 旧接口：**
- `POST /api/scraps`（旧版，走 stock_records 表）废弃，保留兼容期后移除
- `GET /api/scraps`（旧版，查 stock_records WHERE type='报废'）改为读取 scraps 表

### 3.4 Schemas 新增

```python
# ---- 报废（新版） ----
class ScrapCreate(BaseModel):
    asset_id: int = Field(..., gt=0)
    scrap_reason: str = Field(..., min_length=1)  # 'natural_aging' | 'human_damage'
    aging_match: Optional[int] = None             # 1 or 0, natural_aging 时使用
    damage_responsible: Optional[str] = None      # human_damage 时必填
    scrap_date: date
    remark: Optional[str] = None

# ---- 返修入库 ----
class RepairReturnReq(BaseModel):
    pass  # 无需额外字段，后端取当前用户和时间
```

---

## 4. 库存类型扩展

### 4.1 需求概述

在现有入库/出库类型基础上新增「盘盈入库」和「盘亏出库」。

**stock_records.type 字段完整枚举：**

| type | 含义 | 分类 |
|---|---|---|
| `采购入库` | 采购后入库 | 入库 |
| `归还入库` | 领用/借用归还原值 | 入库 |
| `盘盈入库` | 盘点发现账外资产入库 | 入库（新增） |
| `领用出库` | 员工领用 | 出库 |
| `借用出库` | 临时借用 | 出库 |
| `调拨出库` | 调拨到其他仓库 | 出库 |
| `盘亏出库` | 盘点发现资产缺失 | 出库（新增） |
| `调拨` | 仓库间调拨 | 调拨 |
| `归还` | 归还记录 | 归还 |

### 4.2 前端改动

**入库页面（StockIn.vue）：**

入库类型下拉框增加选项：
```text
采购入库
归还入库
盘盈入库   ← 新增
```

**出库页面（StockOut.vue）：**

出库类型下拉框增加选项：
```text
领用出库
借用出库
盘亏出库   ← 新增
```

### 4.3 后端改动

**POST /api/stock/in** — 入库接口

原有 `StockInReq.type` 字段校验扩展为允许 `盘盈入库`。

盘盈入库时：
- 资产状态更新为 `in_stock`
- `to_warehouse_id` 必填（入库仓库）
- remark 建议填写「盘点盘盈，账外资产入库」

**POST /api/stock/out** — 出库接口

原有 `StockOutReq.type` 字段校验扩展为允许 `盘亏出库`.

盘亏出库时：
- 资产状态更新为 `scrapped`（盘亏等同于资产灭失）
- remark 建议填写「盘点盘亏，资产缺失」

### 4.4 Schemas 变更

```python
# StockInReq.type 校验扩展（代码层）
# 允许值：'采购入库' | '归还入库' | '盘盈入库'

# StockOutReq.type 校验扩展（代码层）
# 允许值：'领用出库' | '借用出库' | '盘亏出库'
```

不需要新增 Schema 类，仅扩展现有字段的合法值范围。

---

## 5. 资产领用审批流

### 5.1 approvals 表设计

```sql
CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL REFERENCES assets(id),
    applicant_id INTEGER NOT NULL REFERENCES users(id),       -- 申请人
    dept_id INTEGER NOT NULL REFERENCES departments(id),      -- 申请部门
    type VARCHAR(20) NOT NULL DEFAULT 'borrow',               -- borrow（领用）/ return（归还）
    status VARCHAR(20) NOT NULL DEFAULT 'pending',            -- pending / approved / rejected / delivered
    reason VARCHAR(500),                                      -- 申请理由
    approver_id INTEGER REFERENCES users(id),                 -- 审批人
    approve_time DATETIME,                                    -- 审批时间
    approve_remark VARCHAR(500),                              -- 审批意见
    deliverer_id INTEGER REFERENCES users(id),                -- 出库确认人
    deliver_time DATETIME,                                    -- 出库时间
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 自增主键 |
| asset_id | INTEGER FK | 申请领用的资产ID |
| applicant_id | INTEGER FK | 申请人ID（领用人） |
| dept_id | INTEGER FK | 申请部门ID |
| type | VARCHAR(20) | `borrow`（领用）/ `return`（归还） |
| status | VARCHAR(20) | `pending` / `approved` / `rejected` / `delivered` |
| reason | VARCHAR(500) | 申请理由 |
| approver_id | INTEGER FK | 审批人ID |
| approve_time | DATETIME | 审批时间 |
| approve_remark | VARCHAR(500) | 审批意见 |
| deliverer_id | INTEGER FK | 出库确认人ID（资产管理员） |
| deliver_time | DATETIME | 出库时间 |
| create_time | DATETIME | 申请时间 |

### 5.2 状态流转

```
pending ──主管审批通过──> approved ──管理员确认出库──> delivered
  │                          │
  └──主管审批拒绝──> rejected  └──出库失败回退──> approved
```

- `pending`：用户提交申请，等待部门主管审批
- `approved`：主管审批通过，等待资产管理员出库
- `rejected`：主管审批拒绝（终态）
- `delivered`：管理员确认出库完成（终态）

### 5.3 API 接口

**POST /api/approvals** — 提交领用申请

权限：所有登录用户

Request body：
```json
{
  "asset_id": 1,
  "type": "borrow",
  "reason": "新员工入职需要办公电脑"
}
```

业务逻辑：
1. 校验资产 status == `in_stock`（在库才可申请）
2. 校验该资产无进行中的审批（同一资产不可重复申请）
3. 自动填入 `applicant_id`（当前用户）、`dept_id`（当前用户所属部门）
4. 状态初始为 `pending`

Response：
```json
{
  "code": 0,
  "message": "申请已提交，等待部门主管审批",
  "data": { "id": 1 }
}
```

**GET /api/approvals** — 审批列表

权限：`admin` / `asset_manager` / `dept_manager`（部门主管仅见本部门申请）

查询参数：`?status=pending&page=1&page_size=20`

响应：
```json
{
  "code": 0,
  "data": {
    "total": 10,
    "items": [
      {
        "id": 1,
        "asset_id": 1,
        "asset_no": "IT-202601-0001",
        "asset_name": "ThinkPad X1 Carbon",
        "applicant_id": 3,
        "applicant_name": "张三",
        "dept_id": 2,
        "dept_name": "技术部",
        "type": "borrow",
        "status": "pending",
        "reason": "新员工入职需要办公电脑",
        "approver_name": null,
        "create_time": "2026-05-18 09:00:00"
      }
    ]
  }
}
```

**PUT /api/approvals/{id}/approve** — 主管审批

权限：`admin` / `dept_manager`（部门主管仅可审批本部门申请）

Request body：
```json
{
  "action": "approve",
  "remark": "同意领用"
}
```

`action` 取值：`approve` / `reject`

业务逻辑：
1. 校验审批单 status == `pending`
2. 部门主管校验：`approval.dept_id` == 当前主管的 `dept_id`
3. 更新 `approver_id`、`approve_time`、`approve_remark`
4. `action=approve` → status 变为 `approved`
5. `action=reject` → status 变为 `rejected`

Response：
```json
{
  "code": 0,
  "message": "审批通过"
}
```

**PUT /api/approvals/{id}/deliver** — 管理员确认出库

权限：`admin` / `asset_manager`

Request body：
```json
{}
```

业务逻辑：
1. 校验审批单 status == `approved`
2. 校验资产 status == `in_stock`
3. 自动生成 stock_record（type = 领用出库）
4. 更新资产：`status = in_use`、`dept_id`、`user_id`
5. 更新审批单：`deliverer_id`、`deliver_time`、status → `delivered`

Response：
```json
{
  "code": 0,
  "message": "出库完成",
  "data": { "stock_record_id": 5 }
}
```

### 5.4 Schemas 新增

```python
class ApprovalCreate(BaseModel):
    asset_id: int = Field(..., gt=0)
    type: str = "borrow"          # 'borrow' | 'return'
    reason: Optional[str] = None

class ApprovalAction(BaseModel):
    action: str = Field(..., min_length=1)   # 'approve' | 'reject'
    remark: Optional[str] = None
```

---

## 6. 折旧计算

### 6.1 assets 表新增字段

```sql
ALTER TABLE assets ADD COLUMN depreciation_method VARCHAR(20) DEFAULT 'straight_line';
ALTER TABLE assets ADD COLUMN monthly_depreciation DECIMAL(12,2) DEFAULT 0;
ALTER TABLE assets ADD COLUMN accumulated_depreciation DECIMAL(12,2) DEFAULT 0;
ALTER TABLE assets ADD COLUMN net_value DECIMAL(12,2) DEFAULT 0;
ALTER TABLE assets ADD COLUMN last_depreciation_date DATE;
```

| 字段 | 类型 | 说明 |
|---|---|---|
| depreciation_method | VARCHAR(20) | `straight_line`（年限平均法）/ `one_time`（一次性摊销） |
| monthly_depreciation | DECIMAL(12,2) | 月折旧额 |
| accumulated_depreciation | DECIMAL(12,2) | 累计折旧额 |
| net_value | DECIMAL(12,2) | 资产净值（purchase_price - accumulated_depreciation） |
| last_depreciation_date | DATE | 上次折旧计算日期 |

### 6.2 折旧方法说明

#### 年限平均法（straight_line）

```
月折旧额 = purchase_price / (purchase_lifespan_years × 12)
```

- 前提：`purchase_lifespan_years > 0`
- 每月计提一次，直到 `accumulated_depreciation >= purchase_price`（残值为 0）
- `net_value = purchase_price - accumulated_depreciation`

#### 一次性摊销（one_time）

```
月折旧额 = purchase_price
```

- 入账当月一次性全额计提
- `accumulated_depreciation = purchase_price`
- `net_value = 0`
- 适用于低值易耗品

### 6.3 折旧计算触发

**手动触发：POST /api/assets/depreciation/calculate**

Request body：
```json
{
  "asset_ids": [1, 2, 3]
}
```

`asset_ids` 为空数组或不传则计算所有符合条件的资产（status 不为 scrapped）。

业务逻辑：
1. 筛选 `depreciation_method` 不为空、`purchase_lifespan_years > 0`（年限平均法）、status != scrapped 的资产
2. 计算本期应计提月数 = （当前月份 - 上次折旧月份）或从 purchase_date 起算
3. 本期折旧额 = monthly_depreciation × 月数
4. 更新 `accumulated_depreciation`、`net_value`、`last_depreciation_date`
5. 已提满折旧（accumulated_depreciation >= purchase_price）的资产跳过

Response：
```json
{
  "code": 0,
  "message": "折旧计算完成",
  "data": {
    "processed": 45,
    "skipped": 2,
    "total_depreciation": 12500.00
  }
}
```

**定时触发**：无需后端 cron。前端仪表盘展示一个「计提折旧」按钮，由资产管理员每月手动触发。亦可通过操作系统的 cron/task scheduler 调用 API。

### 6.4 折旧报表

**GET /api/reports/depreciation**

查询参数：`?dept_id=&category_id=&start_date=&end_date=&page=1&page_size=20`

响应：
```json
{
  "code": 0,
  "data": {
    "summary": {
      "total_original_value": 500000.00,
      "total_accumulated_depreciation": 125000.00,
      "total_net_value": 375000.00
    },
    "items": [
      {
        "id": 1,
        "asset_no": "IT-202501-0001",
        "asset_name": "ThinkPad X1 Carbon",
        "purchase_price": 12000.00,
        "purchase_date": "2025-01-15",
        "purchase_lifespan_years": 3,
        "depreciation_method": "straight_line",
        "monthly_depreciation": 333.33,
        "accumulated_depreciation": 5333.28,
        "net_value": 6666.72,
        "depreciation_rate": "44.4%"
      }
    ]
  }
}
```

**折旧率** = `accumulated_depreciation / purchase_price × 100%`

---

## 7. 保修到期提醒

### 7.1 仪表盘新增统计卡片

在现有仪表盘统计卡片区域新增一张卡片：

| 卡片 | 图标 | 数据源 |
|---|---|---|
| 即将过保 | ⚠️ | `GET /api/assets/warranty-alerts?days=30` 返回的数量 |

点击卡片跳转到保修资产列表页。

### 7.2 API 接口

**GET /api/assets/warranty-alerts**

查询参数：`?days=30`（默认 30 天，指未来 days 天内到期的资产）

响应：
```json
{
  "code": 0,
  "data": {
    "total": 5,
    "items": [
      {
        "id": 1,
        "asset_no": "IT-202401-0005",
        "name": "Dell 服务器",
        "warranty_date": "2026-06-15",
        "days_remaining": 28,
        "dept_name": "技术部",
        "user_name": "张三",
        "status": "expiring"
      },
      {
        "id": 2,
        "asset_no": "IT-202312-0012",
        "name": "HP 打印机",
        "warranty_date": "2025-12-01",
        "days_remaining": -169,
        "dept_name": "行政部",
        "user_name": null,
        "status": "expired"
      }
    ]
  }
}
```

`status` 字段：
- `expiring`：`0 <= days_remaining <= days`
- `expired`：`days_remaining < 0`（已过保）
- `days_remaining` = `warranty_date - 今天`（天数）

### 7.3 前端展示

- 仪表盘卡片显示「即将过保：5 台」
- 点击卡片进入保修资产列表页（或使用资产列表页筛选 `warranty_expiring` + `warranty_expired` 状态 tab）
- 列表用颜色标记：黄色（30 天内到期）、红色（已过期）

---

## 8. 通知中心

### 8.1 notifications 表设计

```sql
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),    -- 接收通知的用户（NULL 表示全员）
    type VARCHAR(30) NOT NULL,                         -- 通知类型
    title VARCHAR(200) NOT NULL,                       -- 通知标题
    content VARCHAR(500),                              -- 通知内容
    related_id INTEGER,                                -- 关联业务ID（资产ID、审批ID等）
    related_type VARCHAR(30),                          -- 关联业务类型（asset/approval/repair）
    is_read INTEGER DEFAULT 0,                         -- 0=未读 / 1=已读
    read_time DATETIME,                                -- 阅读时间
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 自增主键 |
| user_id | INTEGER FK | 接收人ID（NULL 表示全员通知） |
| type | VARCHAR(30) | 通知类型枚举 |
| title | VARCHAR(200) | 通知标题 |
| content | VARCHAR(500) | 通知内容 |
| related_id | INTEGER | 关联业务ID |
| related_type | VARCHAR(30) | 关联业务类型 |
| is_read | INTEGER | 0=未读 / 1=已读 |
| read_time | DATETIME | 阅读时间 |
| create_time | DATETIME | 创建时间 |

### 8.2 通知类型

| type | 触发时机 | 接收人 |
|---|---|---|
| `warranty_expiring` | 保修到期前 30 天 | 管理员、资产管理员 |
| `warranty_expired` | 保修到期 | 管理员、资产管理员 |
| `stock_low` | 库存低于预警阈值 | 管理员、资产管理员 |
| `approval_pending` | 提交领用申请 | 部门主管（申请人所在部门） |
| `approval_approved` | 审批通过 | 申请人 |
| `approval_rejected` | 审批拒绝 | 申请人 |
| `repair_completed` | 维修完成 | 资产使用人、管理员 |

### 8.3 通知生成

通知由后端在业务操作中自动生成，不由前端主动调用。触发点：

1. **保修到期**：每日首次访问仪表盘时，后端检查 warranty_date 在未来 30 天内的资产，生成通知（已生成过的跳过）
2. **库存不足**：出入库操作后触发库存计算，低于预警阈值时生成
3. **审批相关**：审批流各状态变更时即时生成
4. **维修完成**：PUT /api/repairs/{id} 且 status 变更为 `finished` 时生成

### 8.4 API 接口

**GET /api/notifications**

查询参数：`?is_read=0&page=1&page_size=20`

权限：登录用户（仅返回当前用户 + 全员通知）

响应：
```json
{
  "code": 0,
  "data": {
    "total": 8,
    "unread_count": 3,
    "items": [
      {
        "id": 1,
        "type": "warranty_expiring",
        "title": "资产保修即将到期",
        "content": "ThinkPad X1 Carbon（IT-202401-0020）保修将于 30 天后到期",
        "related_id": 20,
        "related_type": "asset",
        "is_read": 0,
        "create_time": "2026-05-18 08:00:00"
      }
    ]
  }
}
```

**PUT /api/notifications/{id}/read** — 标记已读

权限：通知接收人本人

Response：
```json
{
  "code": 0,
  "message": "已标记为已读"
}
```

**PUT /api/notifications/read-all** — 全部标记已读

权限：登录用户

Response：
```json
{
  "code": 0,
  "message": "已全部标记为已读",
  "data": { "count": 5 }
}
```

### 8.5 前端展示

- 顶部导航栏右侧铃铛图标（el-bell）
- 未读消息红点徽标（el-badge），数字显示未读数
- 点击铃铛展开下拉通知列表（el-popover），最近 10 条
- 每条通知可点击跳转到关联业务页面
- 底部「全部已读」和「查看全部」按钮
- 独立通知列表页：`/notifications`，分页展示所有通知

---

## 9. 数据导出

### 9.1 导出方式

所有列表接口支持两种导出方式。

#### 方式一：查询参数 `?format=csv`

在现有列表接口增加 `format` 参数：

| 接口 | 导出示例 |
|---|---|
| `GET /api/assets` | `GET /api/assets?format=csv&status=in_stock` |
| `GET /api/stock/records` | `GET /api/stock/records?format=csv&type=领用出库` |
| `GET /api/stock/query` | `GET /api/stock/query?format=csv&warehouse_id=1` |
| `GET /api/repairs` | `GET /api/repairs?format=csv` |
| `GET /api/scraps` | `GET /api/scraps?format=csv` |
| `GET /api/approvals` | `GET /api/approvals?format=csv&status=delivered` |
| `GET /api/reports/depreciation` | `GET /api/reports/depreciation?format=csv` |

`format=csv` 时：
- 不分页，返回当前筛选条件下的全部数据（上限 10000 条）
- Response Content-Type: `text/csv; charset=utf-8-sig`（BOM 头确保 Excel 正确识别中文）
- Content-Disposition: `attachment; filename=assets_20260518.csv`

#### 方式二：独立 `/export` 端点

```text
GET /api/assets/export          → 等同于原 GET /api/assets/export/all
GET /api/stock/export           → 新增，导出出入库记录
GET /api/repairs/export         → 新增，导出维修记录
GET /api/scraps/export          → 新增，导出报废记录
GET /api/approvals/export       → 新增，导出审批记录
GET /api/reports/export/depreciation → 新增，导出折旧报表
```

格式统一为 Excel (.xlsx)，含表头格式（加粗、背景色）。

### 9.2 前端改动

每个数据表格右上角增加「导出」按钮：

- 主按钮文案「导出 Excel」→ 调用 `/export` 端点
- 下拉菜单可选「导出 CSV」→ 调用 `?format=csv`

点击后触发浏览器下载，无需弹窗预览。

---

## 10. 资产盘点联动（盘盈/盘亏）

### 10.1 需求概述

在盘点页面（现有 CheckPlan.vue）增强功能，支持逐个资产标记盘点结果，确认后自动生成对应 stock_record 并更新资产状态。

### 10.2 盘点流程

```
1. 创建盘点计划（选择仓库、分类范围）
2. 系统生成待盘点资产列表
3. 逐项标记：正常 / 盘盈 / 盘亏
4. 提交盘点结果 → 系统自动处理
```

### 10.3 check_plans 表设计（扩展原概念）

盘点计划表（已有 check_plan Schema，补充数据库定义）：

```sql
CREATE TABLE IF NOT EXISTS check_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,                -- 盘点计划名称
    warehouse_id INTEGER REFERENCES warehouses(id),
    category_id INTEGER REFERENCES categories(id),
    status VARCHAR(20) DEFAULT 'pending',       -- pending / in_progress / completed
    remark VARCHAR(500),
    creator_id INTEGER REFERENCES users(id),
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    complete_time DATETIME
);
```

盘点明细表（新增）：

```sql
CREATE TABLE IF NOT EXISTS check_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL REFERENCES check_plans(id) ON DELETE CASCADE,
    asset_id INTEGER NOT NULL REFERENCES assets(id),
    expected_status VARCHAR(20),                -- 应有状态（来自资产当前状态）
    check_result VARCHAR(20) DEFAULT 'pending', -- pending / match / surplus / shortage
    check_remark VARCHAR(500),                  -- 盘点备注
    operator_id INTEGER REFERENCES users(id),
    check_time DATETIME
);
```

| check_result | 含义 |
|---|---|
| `pending` | 待盘点 |
| `match` | 正常（账实相符） |
| `surplus` | 盘盈（账外资产，实际存在但系统无记录） |
| `shortage` | 盘亏（资产缺失，系统有记录但实际不存在） |

### 10.4 API 接口

**POST /api/check-plans** — 创建盘点计划

Request body：
```json
{
  "name": "2026年5月主仓库盘点",
  "warehouse_id": 1,
  "category_id": null,
  "remark": "季度例行盘点"
}
```

Response：
```json
{
  "code": 0,
  "message": "盘点计划已创建",
  "data": { "id": 1, "asset_count": 128 }
}
```

后端逻辑：根据筛选条件（仓库/分类），将该范围内所有资产（status != scrapped）生成 check_items，每条 `check_result = 'pending'`。

**GET /api/check-plans** — 盘点计划列表

响应：
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "2026年5月主仓库盘点",
        "warehouse_name": "主仓库",
        "status": "in_progress",
        "asset_count": 128,
        "checked_count": 45,
        "match_count": 40,
        "surplus_count": 2,
        "shortage_count": 3,
        "create_time": "2026-05-18"
      }
    ]
  }
}
```

**GET /api/check-plans/{id}/items** — 获取盘点明细

查询参数：`?check_result=&page=1&page_size=20`

响应：
```json
{
  "code": 0,
  "data": {
    "total": 128,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "asset_id": 5,
        "asset_no": "IT-202501-0005",
        "asset_name": "ThinkPad X1 Carbon",
        "expected_status": "in_use",
        "expected_location": "技术部-张三",
        "check_result": "pending",
        "check_remark": null
      }
    ]
  }
}
```

**PUT /api/check-plans/{plan_id}/items/{item_id}** — 标记盘点结果

Request body：
```json
{
  "check_result": "match",
  "check_remark": "正常使用中"
}
```

**POST /api/check-plans/{id}/complete** — 提交盘点结果

Request body：
```json
{}
```

业务逻辑：
1. 将 plan status 变更为 `completed`
2. 遍历所有 check_items：
   - `check_result = surplus`：自动调用 stock_in（type = 盘盈入库），若该资产为全新账外资产则需管理员在后续手动创建再入库
   - `check_result = shortage`：自动调用 stock_out（type = 盘亏出库），资产状态变为 scrapped
   - 盘盈盘亏操作均记录 operation_log

Response：
```json
{
  "code": 0,
  "message": "盘点提交完成",
  "data": {
    "surplus_generated": 2,
    "shortage_processed": 3,
    "match_count": 40
  }
}
```

### 10.5 前端交互

- 盘点计划列表页：显示各计划进度条
- 盘点明细页：表格逐行显示资产信息 + 操作按钮（正常/盘盈/盘亏）
- 盘亏标记时弹出原因输入框
- 提交盘点结果时弹窗确认，显示盘盈盘亏数量汇总
- 提交成功后自动跳转回盘点列表

---

## 附录 A：完整 API 端点一览

### 认证模块
| Method | Path | 说明 | 角色变更 |
|---|---|---|---|
| POST | `/api/auth/login` | 登录 | 无变更 |
| POST | `/api/auth/logout` | 登出 | 无变更 |
| GET | `/api/auth/current` | 当前用户 | 无变更 |

### 资产管理
| Method | Path | 说明 | 角色变更 |
|---|---|---|---|
| GET | `/api/assets` | 资产列表 | `require_role(admin, asset_manager, dept_manager, auditor)` + `require_dept_scope()` |
| GET | `/api/assets/names` | 资产名称自动补全 | 登录用户 |
| GET | `/api/assets/{id}` | 资产详情 | `require_role(admin, asset_manager, dept_manager, auditor)` + `require_dept_scope()` |
| GET | `/api/assets/{id}/timeline` | **新增** 资产时间线 | 登录用户 |
| POST | `/api/assets` | 登记资产 | `require_role(admin, asset_manager)` |
| PUT | `/api/assets/{id}` | 编辑资产 | `require_role(admin, asset_manager)` |
| DELETE | `/api/assets/{id}` | 删除资产 | `require_role(admin)` |
| GET | `/api/assets/qrcode/{id}` | 二维码 | 登录用户 |
| GET | `/api/assets/import/template` | 导入模板 | `require_role(admin, asset_manager)` |
| POST | `/api/assets/import` | 导入资产 | `require_role(admin, asset_manager)` |
| GET | `/api/assets/export` | **新增** 导出资产 | `require_role(admin, asset_manager, auditor)` |
| GET | `/api/assets/warranty-alerts` | **新增** 保修提醒 | `require_role(admin, asset_manager, auditor)` |

### 库存管理
| Method | Path | 说明 | 角色变更 |
|---|---|---|---|
| GET | `/api/stock/query` | 库存查询 | `require_role(admin, asset_manager, dept_manager, auditor)` + `require_dept_scope()` |
| POST | `/api/stock/in` | 入库（含盘盈） | `require_role(admin, asset_manager)` |
| POST | `/api/stock/out` | 出库（含盘亏） | `require_role(admin, asset_manager)` |
| POST | `/api/stock/return/{id}` | 归还 | `require_role(admin, asset_manager)` |
| POST | `/api/stock/transfer` | 调拨 | `require_role(admin, asset_manager)` |
| GET | `/api/stock/records` | 出入库记录 | `require_role(admin, asset_manager, dept_manager, auditor)` |
| GET | `/api/stock/export` | **新增** 导出记录 | `require_role(admin, asset_manager, auditor)` |

### 维保管理
| Method | Path | 说明 | 角色变更 |
|---|---|---|---|
| GET | `/api/repairs` | 维修列表 | `require_role(admin, asset_manager, dept_manager, auditor)` |
| POST | `/api/repairs` | 创建维修（扩展字段） | `require_role(admin, asset_manager)` |
| PUT | `/api/repairs/{id}` | 更新维修 | `require_role(admin, asset_manager)` |
| POST | `/api/repairs/{id}/return` | **新增** 返修入库确认 | `require_role(admin, asset_manager)` |
| GET | `/api/scraps` | 报废列表（新表） | `require_role(admin, asset_manager, dept_manager, auditor)` |
| POST | `/api/scraps` | 报废登记（新表） | `require_role(admin, asset_manager)` |
| GET | `/api/repairs/export` | **新增** 导出维修 | `require_role(admin, asset_manager, auditor)` |
| GET | `/api/scraps/export` | **新增** 导出报废 | `require_role(admin, asset_manager, auditor)` |

### 审批流
| Method | Path | 说明 | 角色 |
|---|---|---|---|
| POST | `/api/approvals` | **新增** 提交申请 | 登录用户 |
| GET | `/api/approvals` | **新增** 审批列表 | `require_role(admin, asset_manager, dept_manager)`（主管仅本部门） |
| GET | `/api/approvals/{id}` | **新增** 审批详情 | 申请人/审批人/管理员 |
| PUT | `/api/approvals/{id}/approve` | **新增** 审批 | `require_role(admin, dept_manager)`（主管仅本部门） |
| PUT | `/api/approvals/{id}/deliver` | **新增** 确认出库 | `require_role(admin, asset_manager)` |
| GET | `/api/approvals/export` | **新增** 导出审批 | `require_role(admin, asset_manager, auditor)` |

### 报表统计
| Method | Path | 说明 | 角色变更 |
|---|---|---|---|
| GET | `/api/report/summary` | 资产汇总 | `require_role(admin, asset_manager, dept_manager, auditor)` + `require_dept_scope()` |
| GET | `/api/report/stock` | 库存统计 | 同上 |
| GET | `/api/report/inout` | 出入库报表 | 同上 |
| GET | `/api/reports/depreciation` | **新增** 折旧报表 | 同上 |
| GET | `/api/reports/export/depreciation` | **新增** 导出折旧 | `require_role(admin, asset_manager, auditor)` |

### 通知中心
| Method | Path | 说明 | 角色 |
|---|---|---|---|
| GET | `/api/notifications` | **新增** 通知列表 | 登录用户 |
| PUT | `/api/notifications/{id}/read` | **新增** 标记已读 | 通知接收人 |
| PUT | `/api/notifications/read-all` | **新增** 全部已读 | 登录用户 |

### 盘点
| Method | Path | 说明 | 角色 |
|---|---|---|---|
| POST | `/api/check-plans` | **新增** 创建盘点计划 | `require_role(admin, asset_manager)` |
| GET | `/api/check-plans` | **新增** 盘点计划列表 | `require_role(admin, asset_manager, dept_manager, auditor)` |
| GET | `/api/check-plans/{id}` | **新增** 盘点计划详情 | 同上 |
| GET | `/api/check-plans/{id}/items` | **新增** 盘点明细 | 同上 |
| PUT | `/api/check-plans/{plan_id}/items/{item_id}` | **新增** 标记盘点结果 | `require_role(admin, asset_manager)` |
| POST | `/api/check-plans/{id}/complete` | **新增** 提交盘点 | `require_role(admin, asset_manager)` |

### 折旧
| Method | Path | 说明 | 角色 |
|---|---|---|---|
| POST | `/api/assets/depreciation/calculate` | **新增** 计提折旧 | `require_role(admin, asset_manager)` |

### 系统管理（无变更，仅权限强化）
| Method | Path | 说明 | 角色 |
|---|---|---|---|
| GET/POST/PUT/DELETE | `/api/departments` | 部门管理 | CUD: `admin`, R: `admin/auditor` |
| GET/POST/PUT/DELETE | `/api/categories` | 分类管理 | CUD: `admin`, R: `admin/auditor` |
| GET/POST/PUT/DELETE | `/api/suppliers` | 供应商管理 | CUD: `admin`, R: `admin/auditor` |
| GET/POST/PUT/DELETE | `/api/warehouses` | 仓库管理 | CUD: `admin`, R: `admin/auditor` |
| GET/POST/PUT/DELETE | `/api/warnings` | 预警规则 | CUD: `admin/asset_manager`, R: `admin/asset_manager/auditor` |
| GET | `/api/logs` | 操作日志 | `admin/auditor` |
| GET/POST/PUT/DELETE | `/api/users` | 用户管理 | `admin` |
| PUT | `/api/users/{id}/password` | 重置密码 | `admin` |
| GET/POST/PUT/DELETE | `/api/dict/*` | 数据字典 | CUD: `admin`, R: `admin/auditor` |

---

## 附录 B：数据库变更汇总

### 新增表

| 表名 | 说明 |
|---|---|
| `approvals` | 资产领用审批单 |
| `scraps` | 报废记录（独立于 stock_records） |
| `notifications` | 通知消息 |
| `check_plans` | 盘点计划 |
| `check_items` | 盘点明细 |

### 修改表

| 表名 | 变更内容 |
|---|---|
| `users` | 新增 `dept_id`（FK → departments），role 扩展为 5 种枚举 |
| `assets` | 新增 `depreciation_method`、`monthly_depreciation`、`accumulated_depreciation`、`net_value`、`last_depreciation_date` |
| `repairs` | 新增 `repair_method`、`return_date`、`return_operator_id` |

### 废弃表（数据迁移后移除）

| 表名 | 说明 |
|---|---|
| 无 | `stock_records` 中 `type='报废'` 的记录不再使用，迁移至 `scraps` 表后清理 |

---

## 附录 C：前端路由与菜单结构（3.0）

```
├── 仪表盘              /dashboard              icon: el-icon-data-analysis
├── 资产管理
│   ├── 资产列表         /assets                 icon: el-icon-monitor
│   └── 资产登记         /assets/create          icon: el-icon-plus
├── 库存管理
│   ├── 库存查询         /stock/query            icon: el-icon-search
│   ├── 入库管理         /stock/in               icon: el-icon-bottom
│   └── 出库管理         /stock/out              icon: el-icon-top
├── 维保管理
│   ├── 维修记录         /repairs                icon: el-icon-setting
│   └── 报废记录         /scraps                 icon: el-icon-delete
├── 审批管理
│   ├── 我的申请         /approvals/my           icon: el-icon-document
│   └── 待审批           /approvals/pending      icon: el-icon-check (仅 dept_manager/admin 可见)
├── 盘点管理             /check-plans            icon: el-icon-files
├── 报表统计
│   ├── 资产汇总         /reports/summary        icon: el-icon-pie-chart
│   ├── 库存统计         /reports/stock          icon: el-icon-data-board
│   ├── 出入库报表       /reports/inout          icon: el-icon-s-data
│   └── 折旧报表         /reports/depreciation   icon: el-icon-money (新增)
├── 通知中心             /notifications          icon: el-icon-bell (导航栏铃铛入口)
└── 系统管理             (仅 admin 可见)
    ├── 部门管理         /system/departments
    ├── 分类管理         /system/categories
    ├── 仓库管理         /system/warehouses
    ├── 供应商管理       /system/suppliers
    ├── 用户管理         /system/users
    ├── 预警规则         /system/warnings
    ├── 操作日志         /system/logs
    └── 数据字典         /system/dict
```

---

## 附录 D：响应规范

所有 API 统一返回格式：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

- `code = 0`：成功
- `code = 1`：业务错误（校验失败、数据不存在等）
- `code = 2`：权限不足（403）
- `code = 3`：未登录（401）

分页响应统一嵌套在 `data` 中：

```json
{
  "code": 0,
  "data": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": []
  }
}
```
