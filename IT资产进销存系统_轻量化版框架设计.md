# 🖥️ IT资产进销存系统（轻量化版）框架设计

> 版本：1.0 | 日期：2026-05-13 | 设计：龙虾二号：关羽

---

## 一、技术选型（轻量化）

| 层级 | 推荐方案 |
|------|----------|
| **后端** | Python FastAPI + SQLite（单文件，即装即用） |
| **前端** | Vue3 + Element Plus（轻量化 Admin） |
| **部署** | 本地运行 / 打包 .exe |

> 推荐 **FastAPI + SQLite**，最轻量，部署简单，维护成本低

---

## 二、系统架构

```
┌─────────────────────────────────────────────────────────┐
│                      前端 (Vue3 + Element Plus)         │
├─────────────────────────────────────────────────────────┤
│  登录  │  仪表盘  │  资产  │  库存  │  维保  │  报表  │  设置 │
└────────┴─────────┴────────┴────────┴───────┴────────┴───────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                    后端 (FastAPI + SQLite)               │
├─────────────────────────────────────────────────────────┤
│  认证  │  资产服务  │  库存服务  │  报表服务  │  系统服务  │
└────────┴────────────┴────────────┴────────────┴───────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                    数据层 (SQLite 单文件)                 │
└─────────────────────────────────────────────────────────┘
```

---

## 三、功能模块（全面版）- 24个功能

### 📋 基础模块
1. **登录模块** - 本地账户、权限控制
2. **仪表盘** - 资产总览、预警提醒、最近操作

### 🖥️ 资产管理
3. **资产登记** - 新增/编辑/删除资产
4. **资产分类** - 办公设备、网络设备、配件耗材、软件授权
5. **资产标签** - 生成二维码/条形码标签
6. **资产盘点** - 盘点计划、扫码盘点、盘点报表

### 📦 库存管理
7. **库存查询** - 多条件筛选、关键字搜索
8. **入库管理** - 采购入库、借调入库
9. **出库管理** - 领用出库、借用出库
10. **库存预警** - 低库存/高库存提醒
11. **仓库管理** - 多仓库支持

### 🔧 维保管理
12. **维修记录** - 报修、维修、归还
13. **维保提醒** - 保修期到期提醒
14. **报废管理** - 报废申请、审批、记录

### 📊 报表统计
15. **库存统计** - 分类/部门/状态统计
16. **出入库报表** - 明细汇总
17. **折旧报表** - 资产折旧计算
18. **预估价值** - 原值/折旧值/残值统计
19. **趋势分析** - 月度/季度/年度趋势

### 🔗 扩展模块
20. **供应商管理** - 供应商档案
21. **采购管理** - 采购申请、审批
22. **部门/员工管理** - 组织架构
23. **操作日志** - 完整操作记录
24. **数据导入导出** - Excel 导入导出

---

## 四、数据库设计（SQLite）

### 4.1 用户表 (users)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    real_name VARCHAR(50),
    role VARCHAR(20) DEFAULT 'user',  -- admin/user
    status VARCHAR(20) DEFAULT 'active',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 部门表 (departments)
```sql
CREATE TABLE departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.3 资产分类表 (categories)
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.4 资产主表 (assets)
```sql
CREATE TABLE assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_no VARCHAR(50) UNIQUE NOT NULL,      -- 资产编号
    name VARCHAR(100) NOT NULL,                 -- 资产名称
    category_id INTEGER NOT NULL,               -- 分类ID
    brand VARCHAR(50),                          -- 品牌
    model VARCHAR(100),                         -- 型号
    serial_no VARCHAR(100),                     -- 序列号
    purchase_price DECIMAL(12,2) DEFAULT 0,    -- 采购价格
    purchase_date DATE,                         -- 采购日期
    useful_life INTEGER DEFAULT 60,             -- 使用年限（月）
    depreciation_rate DECIMAL(5,2) DEFAULT 0.05, -- 月折旧率
    status VARCHAR(20) DEFAULT 'in_stock',      -- 在库/借出/维修/报废
    dept_id INTEGER,                            -- 使用部门
    user_id INTEGER,                            -- 使用人
    warehouse_id INTEGER,                       -- 仓库
    location VARCHAR(100),                      -- 存放位置
    supplier_id INTEGER,                        -- 供应商
    warranty_date DATE,                        -- 保修期到期
    remark VARCHAR(500),
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.5 仓库表 (warehouses)
```sql
CREATE TABLE warehouses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    manager_id INTEGER,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.6 出入库记录表 (stock_records)
```sql
CREATE TABLE stock_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    type VARCHAR(20) NOT NULL,          -- 采购入库/借调入库/领用出库/借用出库/归还/维修/报废
    quantity INTEGER DEFAULT 1,
    from_warehouse_id INTEGER,          -- 来源仓库
    to_warehouse_id INTEGER,           -- 目标仓库
    from_dept_id INTEGER,              -- 来源部门
    to_dept_id INTEGER,                -- 目标部门
    from_user_id INTEGER,              -- 原使用人
    to_user_id INTEGER,                -- 新使用人
    operator_id INTEGER,               -- 操作人
    operate_date DATE,                -- 操作日期
    remark VARCHAR(500),
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.7 维修记录表 (repairs)
```sql
CREATE TABLE repairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    fault_desc VARCHAR(500),            -- 故障描述
    repair_type VARCHAR(20),           -- 维修类型
    repair_cost DECIMAL(10,2) DEFAULT 0, -- 维修费用
    repair_date DATE,                  -- 报修日期
    finish_date DATE,                  -- 维修完成日期
    status VARCHAR(20) DEFAULT 'pending', -- pending/fixing/finished
    operator_id INTEGER,
    remark VARCHAR(500),
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.8 供应商表 (suppliers)
```sql
CREATE TABLE suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    contact VARCHAR(50),
    phone VARCHAR(20),
    address VARCHAR(200),
    remark VARCHAR(500),
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.9 库存预警表 (stock_warnings)
```sql
CREATE TABLE stock_warnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    min_stock INTEGER DEFAULT 10,
    max_stock INTEGER DEFAULT 100,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.10 操作日志表 (operation_logs)
```sql
CREATE TABLE operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    operation_type VARCHAR(50),
    target_table VARCHAR(50),
    target_id INTEGER,
    before_value TEXT,
    after_value TEXT,
    ip_address VARCHAR(50),
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 五、桌面端 UI 设计

```
┌────────────────────────────────────────────────────────────────────┐
│  🖥️ IT资产管理系统                                    [用户: admin] │
├────────┬─────────────────────────────────────────────────────────┤
│        │                                                          │
│ 📊 仪表盘                                                        │
│ 🖥️ 资产管理                                                      │
│   ├─ 资产列表                                                    │
│   ├─ 资产登记                                                    │
│   ├─ 资产盘点                                                    │
│   └─ 标签打印                                                    │
│ 📦 库存管理                                                      │
│   ├─ 库存查询                                                    │
│   ├─ 入库管理                                                    │
│   └─ 出库管理                                                    │
│ 🔧 维保管理                                                      │
│   ├─ 维修记录                                                    │
│   └─ 报废管理                                                    │
│ 📊 报表统计                                                      │
│   ├─ 库存统计                                                    │
│   ├─ 折旧报表                                                    │
│   └─ 预估价值                                                    │
│ ⚙️ 系统管理                                                      │
│   ├─ 部门员工                                                    │
│   ├─ 供应商                                                      │
│   └─ 数据管理                                                    │
│        │                                                          │
│        │  ┌─────────────────────────────────────────────────────┐ │
│        │  │                                                     │ │
│        │  │                  主内容区域                         │ │
│        │  │                                                     │ │
│        │  │                                                     │ │
│        │  └─────────────────────────────────────────────────────┘ │
└────────┴──────────────────────────────────────────────────────────┘
```

---

## 六、API 接口设计

### 认证模块
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/auth/login | POST | 用户登录 |
| /api/auth/logout | POST | 用户登出 |
| /api/auth/current | GET | 获取当前用户 |

### 资产管理
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/assets | GET | 资产列表 |
| /api/assets/{id} | GET | 资产详情 |
| /api/assets | POST | 新增资产 |
| /api/assets/{id} | PUT | 更新资产 |
| /api/assets/{id} | DELETE | 删除资产 |
| /api/assets/import | POST | 导入资产 |
| /api/assets/export | GET | 导出资产 |
| /api/assets/qrcode/{id} | GET | 生成二维码 |

### 库存管理
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/stock/query | GET | 库存查询 |
| /api/stock/in | POST | 入库 |
| /api/stock/out | POST | 出库 |
| /api/stock/transfer | POST | 调拨 |
| /api/stock/warnings | GET | 库存预警 |

### 维保管理
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/repairs | GET | 维修列表 |
| /api/repairs | POST | 新增维修 |
| /api/repairs/{id} | PUT | 更新维修 |
| /api/scraps | GET | 报废列表 |
| /api/scraps | POST | 申请报废 |

### 报表统计
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/report/summary | GET | 资产汇总 |
| /api/report/stock | GET | 库存统计 |
| /api/report/depreciation | GET | 折旧报表 |
| /api/report/value | GET | 预估价值 |
| /api/report/trend | GET | 趋势分析 |
| /api/report/inout | GET | 出入库报表 |

### 系统管理
| 接口 | 方法 | 说明 |
|------|------|------|
| /api/departments | GET | 部门列表 |
| /api/categories | GET | 分类列表 |
| /api/suppliers | GET | 供应商列表 |
| /api/warehouses | GET | 仓库列表 |
| /api/logs | GET | 操作日志 |

---

## 七、核心特性

| 特性 | 说明 |
|------|------|
| 💾 单文件数据库 | SQLite，一个 `.db` 文件搞定 |
| 📦 绿色免安装 | Python + 依赖，打包后发给你 |
| 🔒 数据本地 | 不联网，安全可控 |
| 📥 Excel 导入导出 | 批量操作 |
| 🏷️ 条码打印 | 资产标签 |
| 🔔 消息提醒 | 低库存/维保到期 |
| 📊 完整报表 | 库存/折旧/价值/趋势 |

---

## 八、部署方式

### 方式1：直接运行
```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py

# 访问 http://localhost:8000
```

### 方式2：打包成 .exe（可选）
```bash
pip install pyinstaller
pyinstaller main.spec

# 生成 exe，双击运行
```

---

## 九、版本规划

### V1.0（当前版本）
- [x] 基础框架搭建
- [x] 登录认证
- [x] 资产管理（CRUD）
- [x] 库存查询
- [x] 进出数据管理
- [x] 基础报表

### V1.1
- [ ] 资产盘点功能
- [ ] 批量导入导出
- [ ] 消息通知

### V1.2
- [ ] 供应商管理
- [ ] 采购流程
- [ ] 维保管理

---

*文档生成时间：2026-05-13*
