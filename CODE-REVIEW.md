# IT 资产管理系统 3.0 — 后端代码审查

审查时间：2026-05-18
审查范围：`backend/` 目录下 6 个变更文件

---

## 1. `backend/database.py`

### ✅ 通过项
- **SQL 注入**：所有 DDL / DML 均使用 `?` 占位符，无拼接用户输入。
- **事务一致性**：`init_db()` 中迁移步骤后统一执行 `conn.commit()`，种子数据在独立函数内 `conn.commit()`。
- **迁移安全性**：ALTER TABLE 迁移用 try/except `sqlite3.OperationalError` 包裹，重复执行不报错。
- **depreciation_configs 表**：`category_id` 有 UNIQUE 约束，外键引用 categories(id)，设计合理。
- **WAL + 外键**：`get_db()` 正确启用 WAL 模式和 `foreign_keys=ON`。

### ⚠️ 改进建议
- **`salvage_rate DECIMAL(5,4)`**：精度为 5 位总长、4 位小数，即最大值 9.9999。残值率通常 ≤ 1，够用，但如果未来需要更高精度（如 100% = 1.0000）则恰好到边界。建议改为 `DECIMAL(6,4)` 更安全。

### ❌ 必须修复的问题
无。

---

## 2. `backend/main.py`

### ✅ 通过项
- **路由注册**：整齐的 `include_router` 链，`depreciation.router` 已正确注册。
- **生命周期**：`lifespan` 中调用 `init_db()` 确保启动时建表。
- **CORS**：通过环境变量配置，允许前端开发服务器。

### ⚠️ 改进建议
无。

### ❌ 必须修复的问题
无。

---

## 3. `backend/routers/assets.py`

### ✅ 通过项
- **SQL 注入**：所有查询均使用 `?` 参数化，`{where}` 由内部受控字符串拼接，无用户输入参与。
- **db.close()**：所有路径（正常返回、提前 return）均调用了 `db.close()`。
- **权限检查**：除 `/qrcode/{asset_id}` 外，所有端点均有 `user: dict = Depends(get_current_user)`。
- **折旧计算**：使用了参数化 UPDATE，`depreciation_configs` 优先于资产自身字段，逻辑层次清晰。
- **CSV 导出**：`status_map` 翻译为中文，`StreamingResponse` 正确处理 UTF-8 BOM/编码。

### ⚠️ 改进建议
- **`_format_asset` 中的 `in row.keys()`**：`sqlite3.Row` 支持 `in` 运算符直接判断，无需每次调用 `.keys()`。例如：
  ```python
  # 当前写法（冗长）
  "purchase_lifespan_years": row["purchase_lifespan_years"] if "purchase_lifespan_years" in row.keys() else 0
  # 建议写法
  "purchase_lifespan_years": row["purchase_lifespan_years"] if "purchase_lifespan_years" in row else 0
  ```
  非阻塞，但 5 处同样模式可统一简化。

- **`/qrcode/{asset_id}` 无认证检查**（assets.py:323）：所有其他端点都要求登录，唯独二维码接口公开。如果业务上不需要登录即可扫码，这是合理的；否则应添加 `user: dict = Depends(get_current_user)`。

- **`create_asset` 中 `_log` 与主操作的提交顺序**（assets.py:228-230）：日志 `_log` 内部调用 `db.commit()`，如果主操作 `db.commit()`（第228行）成功但 `_log` 的 commit 失败，日志不丢失（因为日志在 commit 后执行）。但如果 `_log` 成功而后续操作失败，日志已经写入。当前 `create_asset` 没问题（先 commit 数据再写日志），但 **`delete_asset` 中顺序相反**（assets.py:268-270）：
  ```python
  _log(db, user["id"], f"删除资产 ...")   # _log 内部 commit，日志先落盘
  db.execute("DELETE FROM assets WHERE id = ?", ...)
  db.commit()                              # 数据后落盘
  ```
  如果 DELETE 的 commit 失败，日志已记录"删除资产"但资产实际未删除。建议将 `_log` 放到 `db.commit()` 之后。

- **`calculate_depreciation` 重复调用风险**（assets.py:275-319）：函数每次调用都会在现有 `accumulated_depreciation` 上叠加一期月折旧额。如果同月内多次调用，会重复累加。建议在函数开头检查上次计算日期，或添加幂等性保护。

### ❌ 必须修复的问题

#### 3.1 `calculate_depreciation` 中 `lifespan=0` 时 `net = price` 忽略已有累计折旧

**文件**：`backend/routers/assets.py`，第 310 行

当资产没有配置使用年限时（`lifespan == 0`），净值被直接设为 `price`，完全忽略已有的 `accumulated_depreciation`。如果资产之前通过其他方式计算过折旧，`net_value` 会被错误地重置为原值。

```python
# 当前代码（第307-310行）
else:
    monthly = 0
    accumulated = float(a["accumulated_depreciation"] or 0) if "accumulated_depreciation" in a.keys() else 0
    net = price                          # ← 应为 price - accumulated
```

**修复**：

```python
else:
    monthly = 0
    accumulated = float(a["accumulated_depreciation"] or 0) if "accumulated_depreciation" in a.keys() else 0
    net = max(price - accumulated, 0)    # ← 正确扣减已累计折旧
```

---

## 4. `backend/routers/repairs.py`

### ✅ 通过项
- **SQL 注入**：全部使用 `?` 参数化。
- **`repair_type` 白名单校验**：`create_repair` 和 `update_repair` 均校验 `req.repair_type in VALID_REPAIR_TYPES`。
- **事务一致性**：
  - `create_repair`：INSERT repairs + UPDATE assets 状态 在同一 commit（repairs.py:79）。
  - `repair_return`：UPDATE repairs + UPDATE assets 在同一 commit（repairs.py:131）。
- **CSV 导出**：`status_map` 翻译为中文，正确导出。
- **`db.close()`**：所有路径均关闭连接。

### ⚠️ 改进建议
- **`update_repair` 中通知生成前未校验资产是否存在**（repairs.py:104-113）：
  ```python
  asset = db.execute("SELECT asset_no, name FROM assets WHERE id = ?", (existing["asset_id"],)).fetchone()
  for a in admins:
      db.execute(
          "INSERT INTO notifications ...",
          (a["id"], "repair_complete", "维修已完成",
           f"资产 {asset['asset_no']} {asset['name']} 维修已完成，等待返修入库确认", repair_id)
      )
  ```
  如果资产被删除，`asset` 为 `None`，第 111 行会抛出 `TypeError: 'NoneType' object is not subscriptable`。建议加空值检查：
  ```python
  if asset is None:
      db.close()
      return Response(code=1, message="关联资产不存在").model_dump()
  ```

- **`repair_return` 中 `return_date` 类型判断**（repairs.py:128）：`hasattr(req.return_date, 'isoformat')` 可用于区分 `date` 和 `str`，但 `str(req.return_date)` 对两种类型都有效，更简洁。

### ❌ 必须修复的问题
无。

---

## 5. `backend/routers/reports.py`

### ✅ 通过项
- **SQL 注入**：所有动态 SQL（`{where}`）由受控固定字符串拼接，参数始终经 `?` 传递。
- **事务**：只读报表，无写操作，无需 commit。
- **折旧报表**：CSV 输出新增分类列和分类汇总区域，逻辑清晰。
- **db.close()**：所有路径均关闭。
- **状态计算**（reports.py:156）：`"已折旧"/"折旧中"/"未折旧"` 三级状态合理。

### ⚠️ 改进建议
- **`depreciation_report` 中 `in a.keys()` 写法**：与 `assets.py` 中同样问题，`sqlite3.Row` 直接支持 `in`，可简化为 `"field" in a`。

- **CSV 分类汇总的空行**（reports.py:178）：`writer.writerow([])` 写空行分隔明细与汇总，这是合理的格式设计，无问题。

### ❌ 必须修复的问题
无。

---

## 6. `backend/routers/depreciation.py`（新文件）

### ✅ 通过项
- **SQL 注入**：全部 `?` 参数化。
- **UPSERT 模式**：`save_config` 用 SELECT 检查是否存在，再执行 INSERT 或 UPDATE，逻辑清晰。
- **权限检查**：所有端点有 `user: dict = Depends(get_current_user)`。
- **db.close()**：所有路径均关闭连接。
- **Response 类使用**：与项目风格一致。

### ⚠️ 改进建议
- **`delete_config` 不检查记录是否存在**（depreciation.py:57-63）：
  ```python
  def delete_config(config_id: int, user: dict = Depends(get_current_user)):
      db = get_db()
      db.execute("DELETE FROM depreciation_configs WHERE id = ?", (config_id,))
      db.commit()
      db.close()
      return Response(message="删除成功").model_dump()
  ```
  删除不存在的 ID 也返回"删除成功"，对用户不够友好。建议增加存在性检查：
  ```python
  existing = db.execute("SELECT id FROM depreciation_configs WHERE id = ?", (config_id,)).fetchone()
  if not existing:
      db.close()
      return Response(code=1, message="配置不存在").model_dump()
  ```

- **`save_config` 未校验 `category_id` 是否存在**：如果传入无效的 `category_id`，会静默创建孤儿配置。可添加分类存在性检查，但非必须（有外键约束兜底，INSERT 时会报错）。

### ❌ 必须修复的问题

#### 6.1 导入路径与项目其他路由文件不一致

**文件**：`backend/routers/depreciation.py`，第 4 行

```python
# depreciation.py 的写法（不一致）
from routers.auth import get_current_user

# 所有其他 router 文件的写法（一致）
from auth import get_current_user
```

项目中 `assets.py`、`repairs.py`、`reports.py` 等所有其他路由文件都使用 `from auth import get_current_user`，唯独 `depreciation.py` 使用了 `from routers.auth import get_current_user`。虽然两种写法在启动时都可能工作（取决于 `sys.path`），但这破坏了代码一致性，且 `from routers.auth` 依赖父目录在 `sys.path` 中，耦合更强。应统一为 `from auth import get_current_user`。

**修复**：

```python
# 将第 4 行
from routers.auth import get_current_user
# 改为
from auth import get_current_user
```

---

## 汇总

| 级别 | 数量 | 说明 |
|------|------|------|
| ❌ 必须修复 | 2 | `assets.py:310` net 值计算错误；`depreciation.py:4` 导入路径不一致 |
| ⚠️ 改进建议 | 5 | `_log` 在 delete 中的顺序、update_repair 中 asset 空值检查、delete_config 不检查存在性、qrcode 无认证、重复调用折旧计算无保护 |
| ✅ 通过 | — | SQL 参数化无注入风险、事务边界正确、权限检查完整 |

### 建议修复优先级
1. **`assets.py:310`** — net 值计算错误，直接影响折旧数据的正确性。
2. **`depreciation.py:4`** — 导入路径不一致，可能在特定部署环境下导致 ImportError。
3. 其余改进建议可在后续迭代中处理。
