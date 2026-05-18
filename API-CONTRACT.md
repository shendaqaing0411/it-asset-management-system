# IT 资产管理系统 3.0 — API 契约

> 本文档是前端和后端团队的接口契约。所有端点前缀 `/api`，需 JWT Bearer 认证（除 `/auth/*`）。

---

## 1. 角色权限体系

用户表 `users` 的 `role` 字段扩展为 5 种值：
`super_admin` | `asset_admin` | `dept_manager` | `user` | `auditor`

| 权限 | super_admin | asset_admin | dept_manager | user | auditor |
|------|:--:|:--:|:--:|:--:|:--:|
| 仪表盘 | ✓ | ✓ | 仅本部门 | 仅本人 | 只读全量 |
| 资产 CRUD | ✓ | ✓ | ✗ | ✗ | ✗ |
| 出入库/调拨 | ✓ | ✓ | ✗ | ✗ | ✗ |
| 审批领用 | ✓ | ✓ | 审批本部门 | 提交申请 | ✗ |
| 维修/报废 | ✓ | ✓ | ✗ | 报修 | ✗ |
| 报表 | ✓ | ✓ | 仅本部门 | ✗ | 只读全量 |
| 系统管理 | ✓ | ✗ | ✗ | ✗ | ✗ |
| 数据导出 | ✓ | ✓ | 仅本部门 | ✗ | ✓ |

后端用 `require_role(*roles)` 依赖替代 `if user["role"] != "admin"`。

---

## 2. 资产全生命周期时间线

### GET /api/assets/{id}/timeline

Response:
```json
{
  "code": 0,
  "data": [
    {"time": "2024-03-01", "type": "入库", "detail": "采购入库 → 主仓库", "operator": "管理员"},
    {"time": "2024-06-15", "type": "出库", "detail": "领用出库 → 技术部 / 张三", "operator": "管理员"},
    {"time": "2025-01-10", "type": "维修", "detail": "屏幕损坏 — 送修", "operator": "管理员"},
    {"time": "2025-01-20", "type": "返修入库", "detail": "维修完成，返修入库 → 主仓库", "operator": "管理员"}
  ]
}
```

后端 UNION ALL 合并 `stock_records` + `repairs` + `scraps`，按时间排序返回。

---

## 3. 维保模块重构

### 报废（新独立表 `scraps`）

```sql
CREATE TABLE scraps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    scrap_reason VARCHAR(20) NOT NULL,        -- '自然老化' / '人为损坏'
    aging_match INTEGER DEFAULT 0,            -- 0/1，自然老化时必填
    damage_responsible VARCHAR(50),            -- 人为损坏时必填
    scrap_date DATE NOT NULL,
    remark VARCHAR(500),
    operator_id INTEGER,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);
```

### POST /api/scraps
```json
{
  "asset_id": 1,
  "scrap_reason": "自然老化",
  "aging_match": 1,
  "damage_responsible": null,
  "scrap_date": "2025-06-01",
  "remark": "超过使用年限，无法修复"
}
```
→ 更新 `assets.status = 'scrapped'`，写入 scraps 表，写 operation_log。

### GET /api/scraps?page=1&page_size=20
返回分页列表，JOIN assets 取 asset_no/asset_name。

### 维修增强

repairs 表新增字段：
- `repair_method VARCHAR(20)` — 更换配件/软件修复/清洁保养/返厂维修
- `return_date DATE` — 返修入库日期
- `return_confirmed INTEGER DEFAULT 0` — 是否已确认返修入库

repair_type 值改为枚举：保修期内维修 / 保外维修 / 厂商送修 / 自行维修

### POST /api/repairs/{id}/return
```json
{"return_date": "2025-02-01"}
```
→ 更新 repairs.return_confirmed=1, return_date，assets.status='in_stock'。
**维修完成 ≠ 返修入库**，只有调用此接口才恢复资产状态。

### PUT /api/repairs/{id}
status='finished' 仅标记维修完成，不再自动改资产状态。

---

## 4. 库存类型扩展

stock/in 的 type 增加 `盘盈入库`，stock/out 的 type 增加 `盘亏出库`。

前后端只需在现有枚举列表各加一项，无需改 schema。

---

## 5. 资产领用审批流

```sql
CREATE TABLE approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    applicant_id INTEGER NOT NULL,
    approver_id INTEGER,
    dept_id INTEGER,
    status VARCHAR(20) DEFAULT 'pending',  -- pending/approved/rejected/delivered
    apply_reason VARCHAR(500),
    reject_reason VARCHAR(500),
    apply_date DATE,
    approve_date DATE,
    deliver_date DATE,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id),
    FOREIGN KEY (applicant_id) REFERENCES users(id)
);
```

### POST /api/approvals
```json
{"asset_id": 1, "dept_id": 2, "apply_reason": "新员工入职需要电脑"}
```
→ 普通用户提交申请，role=user 可调用。

### PUT /api/approvals/{id}/approve
```json
{"approved": true, "reject_reason": null}
```
→ dept_manager 审批本部门申请。

### PUT /api/approvals/{id}/deliver
→ admin/asset_admin 确认出库，写 stock_record，更新资产状态。

### GET /api/approvals?status=pending
→ 按角色过滤：普通用户看自己的，主管看本部门的，管理员看全部。

---

## 6. 折旧计算

assets 表新增：
```sql
depreciation_method VARCHAR(20) DEFAULT 'straight',  -- straight/once
monthly_depreciation DECIMAL(12,2) DEFAULT 0,
accumulated_depreciation DECIMAL(12,2) DEFAULT 0,
net_value DECIMAL(12,2) DEFAULT 0
```

POST /api/assets/calculate-depreciation
→ 遍历所有 in_stock/in_use 资产：
- straight: `monthly = purchase_price / (lifespan_years * 12)`，`accumulated += monthly`，`net = purchase_price - accumulated`
- once: 全额折旧

GET /api/reports/depreciation
```json
{
  "code": 0,
  "data": {
    "items": [
      {"asset_no": "IT-001", "name": "ThinkPad", "purchase_price": 8000, "accumulated_depreciation": 4800, "net_value": 3200, "method": "straight", "status": "折旧中"}
    ],
    "summary": {"total_original": 500000, "total_depreciation": 200000, "total_net": 300000}
  }
}
```

---

## 7. 保修到期提醒

### GET /api/assets/warranty-alerts?days=30
返回 warranty_date 在 `[today, today+days]` 范围内的资产列表。
仪表盘卡片显示数量，点击穿透到列表。

---

## 8. 通知中心

```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type VARCHAR(30) NOT NULL,      -- warranty_expire/stock_low/approval_pending/repair_complete
    title VARCHAR(200) NOT NULL,
    content VARCHAR(500),
    is_read INTEGER DEFAULT 0,
    ref_id INTEGER,                  -- 关联的业务 ID
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### GET /api/notifications?unread=1
### PUT /api/notifications/{id}/read
### GET /api/notifications/count — 未读数

---

## 9. 数据导出

所有分页列表接口支持 `?format=csv` 参数：
- GET /api/assets?format=csv
- GET /api/stock/records?format=csv
- GET /api/repairs?format=csv
- GET /api/scraps?format=csv
- GET /api/reports/depreciation?format=csv

返回 `Content-Type: text/csv; charset=utf-8`，文件名 `attachment; filename=xxx.csv`。

---

## 10. 资产盘点联动

### POST /api/stock/check
```json
{
  "items": [
    {"asset_id": 1, "result": "normal"},
    {"asset_id": 2, "result": "surplus", "remark": "盘盈"},
    {"asset_id": 3, "result": "loss", "remark": "盘亏"}
  ]
}
```
result=surplus → 自动生成 stock_record type='盘盈入库'，资产状态→in_stock
result=loss → 自动生成 stock_record type='盘亏出库'，资产状态→scrapped
result=normal → 仅标记盘点时间

---

## 11. 前端路由与菜单变更

### 新增路由
```
/assets/:id/timeline     AssetTimeline   资产时间线
/stock/approvals         ApprovalList    领用审批
/reports/depreciation    Depreciation    折旧报表
/repairs/scraps          ScrapList       报废管理（从独立菜单移到维保子菜单内）
```

### 菜单结构
```
仪表盘
资产管理 → 资产列表 / 资产登记 / 资产盘点
库存管理 → 库存查询 / 入库管理 / 出库管理 / 领用审批
维保管理 → 维修记录 / 报废管理
报表统计 → 库存统计 / 出入库报表 / 资产汇总 / 折旧报表
系统管理 → （不变）+ 数据字典
```

### 全局组件
- `components/NotificationBell.vue` — 铃铛图标 + 未读红点 + 下拉通知列表
- 所有表格页右上角「导出 Excel」按钮
