# IT 资产管理系统 3.0 — 后端 API 逆向/边界测试报告

**测试日期**: 2026-05-18  
**测试环境**: macOS, Python 3.11, SQLite (WAL), FastAPI + Uvicorn  
**测试范围**: CSRF 状态中文化、折旧配置 CRUD、折旧报表、边界/异常输入

---

## 测试结果汇总

| 类别 | 通过 | 失败 |
|------|------|------|
| 功能验证 | 14 | 0 |
| 边界/异常 | 4 | 6 |
| **合计** | **18** | **6** |

---

## A. 登录与认证

### T0: 登录获取 Token ✅ 通过
- **请求**: `POST /api/auth/login` with `{"username":"admin","password":"admin123"}`
- **响应**: `code:0`, 返回 token (JWT) 和用户信息 (username, role: super_admin)
- **结论**: 认证流程正常

---

## B. 资产 CSV 导出 — 中文状态验证

### T1: 资产 CSV 导出状态字段中文化 ✅ 通过
```bash
curl -s "http://localhost:8000/api/assets?format=csv" -H "$AUTH" | head -3
```
- **CSV 表头**: `资产编号,名称,分类,...,状态,...,备注`
- **状态列标题**: `状态` (中文)
- **数据样本状态值**: `在库`, `使用中`, `已报废` — 全部中文
- **结论**: CSV 导出状态字段已中文化，符合预期

---

## C. 维修 CSV 导出 — 中文状态验证

### T2: 维修 CSV 导出状态字段中文化 ✅ 通过
```bash
curl -s "http://localhost:8000/api/repairs?format=csv" -H "$AUTH" | head -3
```
- **CSV 表头**: `资产编号,资产名称,...,维修状态,...`
- **维修状态列标题**: `维修状态` (中文)
- **数据样本状态值**: `已完成`, `待处理` — 全部中文
- **结论**: CSV 导出维修状态字段已中文化，符合预期

---

## D. 折旧配置 CRUD

### T3: 列表（空） ✅ 通过
- **请求**: `GET /api/depreciation-configs`
- **响应**: `{"code":0,"data":[],"message":"ok"}`
- **结论**: 空列表返回正常

### T4: 创建配置 ✅ 通过
- **请求**: `POST /api/depreciation-configs` with `{"category_id":3,"method":"straight","useful_life_years":10,"salvage_rate":0.05}`
- **响应**: `{"code":0,"data":null,"message":"保存成功"}`
- **结论**: 创建成功

### T5: 列表（有数据） ✅ 通过
- **响应**: 返回刚创建的配置，包含 `category_name` 和 `parent_name` JOIN 字段
- **结论**: 列表返回完整关联数据

### T6: 重复创建 → 更新 ✅ 通过
- **请求**: 同一 `category_id=3` 再次 POST，method 改为 "once"，years 改为 5，salvage 改为 0
- **响应**: `{"code":0,"data":null,"message":"保存成功"}`
- **验证**: 列表中 method 从 "straight" 变为 "once"，各字段已更新
- **结论**: Upsert 逻辑正确

### T7: 删除配置 ✅ 通过
- **请求**: `DELETE /api/depreciation-configs/1`
- **响应**: `{"code":0,"data":null,"message":"删除成功"}`
- **验证**: 再次列表返回空 `[]`
- **结论**: 删除功能正常

---

## E. 折旧报表

### T10: 折旧报表 CSV 导出 ✅ 通过
- **CSV 表头**: `资产编号,名称,分类,原值,月折旧额,累计折旧,净值,折旧方法,状态`
- **方法列标题**: `折旧方法` (中文)
- **方法值**: `直线法` (中文)
- **状态值**: `未折旧` (中文)
- **分类汇总区域**: CSV 中包含 `分类汇总` 行，显示各分类的 `原值合计,累计折旧合计,净值合计,资产数量`
- **结论**: 折旧报表 CSV 中文化完成，分类汇总已包含

### T11: 折旧计算 ✅ 通过
- **请求**: `POST /api/assets/calculate-depreciation`
- **响应**: `{"code":0,"data":{"updated":40},"message":"折旧计算完成"}`
- **结论**: 折旧批量计算功能正常

### T13: 折旧报表 JSON 结构 ✅ 通过
- **响应 keys**: `items`, `summary`, `category_summary`
- **category_summary**: 返回 3 个分类汇总条目，每项包含 `category`, `original`, `depreciation`, `net`, `count`
- **summary**: 包含 `total_original`, `total_depreciation`, `total_net`
- **结论**: JSON 报表结构完整，分类汇总与总计汇总均已包含

---

## F. 前端数据需求验证

### T12: 资产列表 remark 字段 ✅ 通过
- **请求**: `GET /api/assets?page=1`
- **验证**: items[0] 包含 `remark` 字段
- **结论**: 资产列表 API 返回 remark 字段，前端可正常使用

### T16: remark 字段有值 ✅ 通过
- **验证**: 抽样查看 remark 字段值，部分为 null（无备注），数据模型正常
- **结论**: remark 字段已正确返回

---

## G. 边界/异常测试

### E1: 删除不存在的配置 ID ❌ 失败 — P1
```bash
curl -s -X DELETE "http://localhost:8000/api/depreciation-configs/99999" -H "$AUTH"
```
- **实际输出**: `{"code":0,"data":null,"message":"删除成功"}`
- **预期输出**: `{"code":1,"message":"配置不存在"}` 或类似错误响应
- **根因**: `DELETE FROM depreciation_configs WHERE id = ?` 在 SQLite 中对不存在行执行仍返回成功，未检查 `cursor.rowcount`
- **严重程度**: P1 — 前端可能误以为操作成功

### E2: 缺少必填字段 ✅ 通过
```bash
curl -s -X POST "http://localhost:8000/api/depreciation-configs" -H "$AUTH" -H 'Content-Type: application/json' -d '{}'
```
- **实际输出**: `{"detail":[{"type":"missing","loc":["body","category_id"],"msg":"Field required","input":{}}]}`
- **预期输出**: 422 参数校验错误
- **结论**: Pydantic 模型校验生效

### E3: 不存在的 category_id ❌ 失败 — P1
```bash
curl -s -X POST "http://localhost:8000/api/depreciation-configs" -H "$AUTH" -H 'Content-Type: application/json' -d '{"category_id":99999,"method":"straight"}'
```
- **实际输出**: `Internal Server Error` (HTTP 500)
- **预期输出**: `{"code":1,"message":"分类不存在"}` 或类似业务错误
- **根因**: `sqlite3.IntegrityError: FOREIGN KEY constraint failed` 未被捕获，直接抛出 500
- **严重程度**: P1 — 500 错误暴露内部异常，用户体验差，且可能泄露系统信息

### E4: 负数残值率 ❌ 失败 — P1
```bash
curl -s -X POST "http://localhost:8000/api/depreciation-configs" -H "$AUTH" -H 'Content-Type: application/json' -d '{"category_id":3,"method":"straight","useful_life_years":5,"salvage_rate":-0.5}'
```
- **实际输出**: `{"code":0,"data":null,"message":"保存成功"}`
- **预期输出**: 校验错误，salvage_rate 必须 >= 0
- **根因**: `DepreciationConfigReq.salvage_rate` 类型为 `Optional[float]`，无 `ge=0` 约束
- **严重程度**: P1 — 业务数据污染风险

### E5: 无 Token 访问 ✅ 通过
```bash
curl -s "http://localhost:8000/api/depreciation-configs"
```
- **实际输出**: `{"detail":[{"type":"missing","loc":["header","authorization"],"msg":"Field required","input":null}]}`
- **结论**: 认证中间件生效

### E6: 负数使用年限 ❌ 失败 — P1
```bash
curl -s -X POST "http://localhost:8000/api/depreciation-configs" -H "$AUTH" -H 'Content-Type: application/json' -d '{"category_id":3,"method":"straight","useful_life_years":-1,"salvage_rate":0}'
```
- **实际输出**: `{"code":0,"data":null,"message":"保存成功"}`
- **预期输出**: 校验错误，useful_life_years 必须 > 0
- **根因**: `DepreciationConfigReq.useful_life_years` 类型为 `Optional[int]`，无 `gt=0` 约束
- **严重程度**: P1 — 业务数据污染风险

### E7: 无效折旧方法 ❌ 失败 — P2
```bash
curl -s -X POST "http://localhost:8000/api/depreciation-configs" -H "$AUTH" -H 'Content-Type: application/json' -d '{"category_id":3,"method":"invalid_method","useful_life_years":5,"salvage_rate":0}'
```
- **实际输出**: `{"code":0,"data":null,"message":"保存成功"}`
- **预期输出**: 校验错误，method 应为枚举值 (straight/once/accelerated)
- **根因**: `method` 定义为 `Optional[str]`，无枚举约束
- **严重程度**: P2 — 影响折旧计算正确性

### E8: 残值率 > 1 ❌ 失败 — P2
```bash
curl -s -X POST "http://localhost:8000/api/depreciation-configs" -H "$AUTH" -H 'Content-Type: application/json' -d '{"category_id":3,"method":"straight","useful_life_years":5,"salvage_rate":1.5}'
```
- **实际输出**: `{"code":0,"data":null,"message":"保存成功"}`
- **预期输出**: 校验错误，salvage_rate 必须 <= 1
- **根因**: 无 `le=1` 约束
- **严重程度**: P2 — 残值率超过 100% 不合理

### E9: SQL 注入 ✅ 通过
```bash
curl -s "http://localhost:8000/api/assets?keyword=%27%3B%20DROP%20TABLE%20assets%3B%20--" -H "$AUTH"
```
- **实际输出**: `{"code":0,"data":{"total":0,...},"message":"ok"}`
- **验证**: 资产表完整，总数仍为 46
- **结论**: 参数化查询有效防止 SQL 注入

### E10: XSS 注入 ✅ 通过
```bash
curl -s "http://localhost:8000/api/assets?keyword=<script>alert('xss')</script>" -H "$AUTH"
```
- **实际输出**: 正常返回，total=0（无匹配结果）
- **结论**: 无 XSS 风险，输入被当作普通搜索关键词处理

---

## 修复建议

### P1 (高优先级)
| # | 问题 | 文件 | 修复方式 |
|---|------|------|----------|
| E1 | DELETE 不存在 ID 返回成功 | `routers/depreciation.py:58-63` | 检查 `cursor.rowcount`，为 0 时返回错误 |
| E3 | 不存在 category_id 返回 500 | `routers/depreciation.py:34-54` | try/except IntegrityError，返回业务错误 |
| E4 | 负数 salvage_rate 被接受 | `routers/depreciation.py:13-16` | `salvage_rate: Optional[float] = Field(default=0, ge=0, le=1)` |
| E6 | 负数 useful_life_years 被接受 | `routers/depreciation.py:13-16` | `useful_life_years: Optional[int] = Field(default=5, gt=0)` |

### P2 (中优先级)
| # | 问题 | 文件 | 修复方式 |
|---|------|------|----------|
| E7 | 无效 method 被接受 | `routers/depreciation.py:13-16` | 使用 `Literal["straight","once","accelerated"]` 约束 |
| E8 | salvage_rate > 1 被接受 | `routers/depreciation.py:13-16` | 同 E4，添加 `le=1` |

---

## 后端进程状态
后端已在测试完成后停止运行。
