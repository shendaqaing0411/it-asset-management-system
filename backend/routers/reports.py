# 报表统计路由：资产汇总、库存统计、出入库报表、折旧报表

import io
import csv
import random
import string
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from database import get_db
from auth import get_current_user, require_permission, require_dept_scope
from schemas import Response

router = APIRouter(prefix="/api/report", tags=["报表统计"])


@router.get("/summary")
def summary(user: dict = Depends(require_permission("report:summary")),
            scope: dict = Depends(require_dept_scope())):
    """资产汇总：按状态统计数量与总价值"""
    db = get_db()
    asset_where = ""
    scope_params = []
    if scope:
        conditions = []
        for k, v in scope.items():
            conditions.append(f"{k} = ?")
            scope_params.append(v)
        asset_where = "WHERE " + " AND ".join(conditions)
    total = db.execute(f"SELECT COUNT(*) FROM assets {asset_where}", scope_params).fetchone()[0]
    def _count(status):
        cond = asset_where.replace("WHERE", "WHERE status = ? AND") if asset_where else f"WHERE status = ?"
        return db.execute(f"SELECT COUNT(*) FROM assets {cond}", scope_params + [status]).fetchone()[0]
    in_stock = _count("in_stock")
    in_use = _count("in_use")
    borrowed = _count("borrowed")
    repairing = _count("repairing")
    scrapped = _count("scrapped")
    total_value = db.execute(f"SELECT COALESCE(SUM(purchase_price), 0) FROM assets {asset_where}", scope_params).fetchone()[0]
    db.close()
    return Response(data={
        "total": total, "in_stock": in_stock, "in_use": in_use,
        "borrowed": borrowed, "repairing": repairing, "scrapped": scrapped,
        "total_value": total_value
    }).model_dump()


@router.get("/stock")
def stock_report(user: dict = Depends(require_permission("report:stock")),
                 scope: dict = Depends(require_dept_scope())):
    db = get_db()
    scope_where = ""
    scope_params = []
    if scope:
        conds = [f"a.{k} = ?" for k, v in scope.items()]
        scope_params = list(scope.values())
        scope_where = "WHERE " + " AND ".join(conds)
    # 按二级类目统计（含一级类目分组信息）
    by_category = db.execute(
        f"""SELECT c.id, c.name, c.parent_id, COUNT(*) as count, COALESCE(SUM(a.purchase_price), 0) as value
           FROM assets a LEFT JOIN categories c ON a.category_id = c.id
           {scope_where}
           GROUP BY a.category_id ORDER BY count DESC""",
        scope_params
    ).fetchall()
    # 按一级类目汇总（含子分类明细）
    by_parent_scope = ""
    by_parent_params = []
    if scope:
        by_parent_scope = "AND " + " AND ".join(f"a.{k} = ?" for k in scope)
        by_parent_params = list(scope.values())
    by_parent = db.execute(
        f"""SELECT p.id as parent_id, p.name as parent_name,
                  c.id as child_id, c.name as child_name,
                  COUNT(a.id) as count, COALESCE(SUM(a.purchase_price), 0) as value
           FROM categories c
           LEFT JOIN categories p ON c.parent_id = p.id
           LEFT JOIN assets a ON a.category_id = c.id
           WHERE c.parent_id > 0 {by_parent_scope}
           GROUP BY c.id
           ORDER BY p.sort_order, c.sort_order""",
        by_parent_params
    ).fetchall()
    by_status = db.execute(
        f"SELECT status, COUNT(*) as count FROM assets {scope_where} GROUP BY status",
        scope_params
    ).fetchall()
    by_dept = db.execute(
        f"SELECT d.name, COUNT(*) as count FROM assets a LEFT JOIN departments d ON a.dept_id = d.id {scope_where} GROUP BY a.dept_id",
        scope_params
    ).fetchall()
    db.close()
    # 构建二级类目树形统计
    tree_data = []
    parent_map = {}
    for r in by_parent:
        rdict = dict(r)
        pid = rdict["parent_id"]
        if pid not in parent_map:
            parent_map[pid] = {
                "name": rdict["parent_name"],
                "id": pid,
                "children": [],
                "count": 0,
                "value": 0
            }
            tree_data.append(parent_map[pid])
        child = {"id": rdict["child_id"], "name": rdict["child_name"], "count": rdict["count"], "value": rdict["value"] or 0}
        parent_map[pid]["children"].append(child)
        parent_map[pid]["count"] += rdict["count"]
        parent_map[pid]["value"] += rdict["value"] or 0
    return Response(data={
        "by_category": [dict(r) for r in by_category],
        "by_status": [dict(r) for r in by_status],
        "by_dept": [dict(r) for r in by_dept],
        "by_sub_category": tree_data
    }).model_dump()


@router.get("/inout")
def inout_report(
    start_date: str = Query(None), end_date: str = Query(None),
    type: str = Query(None),
    user: dict = Depends(require_permission("report:inout")),
    scope: dict = Depends(require_dept_scope())
):
    db = get_db()
    conditions = []
    params = []
    if start_date:
        conditions.append("s.operate_date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("s.operate_date <= ?")
        params.append(end_date)
    if type:
        conditions.append("s.type = ?")
        params.append(type)
    if scope:
        for k, v in scope.items():
            conditions.append(f"a.{k} = ?")
            params.append(v)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    rows = db.execute(
        f"""SELECT s.*, a.asset_no, a.name as asset_name
           FROM stock_records s LEFT JOIN assets a ON s.asset_id = a.id
           {where} ORDER BY s.id DESC LIMIT 500""",
        params
    ).fetchall()
    count_from = "FROM stock_records s LEFT JOIN assets a ON s.asset_id = a.id" if scope else "FROM stock_records s"
    summary = db.execute(
        f"""SELECT s.type, COUNT(*) as count {count_from} {where} GROUP BY s.type""",
        params
    ).fetchall()
    db.close()
    return Response(data={
        "records": [dict(r) for r in rows],
        "summary": [dict(r) for r in summary]
    }).model_dump()


@router.get("/depreciation")
def depreciation_report(format: str = Query(None),
                         user: dict = Depends(require_permission("report:depreciation")),
                         scope: dict = Depends(require_dept_scope())):
    """折旧报表：列出所有资产折旧状态及汇总，按分类分组"""
    db = get_db()
    scope_where = ""
    scope_params = []
    if scope:
        conds = [f"a.{k} = ?" for k, v in scope.items()]
        scope_params = list(scope.values())
        scope_where = "WHERE " + " AND ".join(conds)
    rows = db.execute(
        f"""SELECT a.*, c.name as category_name,
                  (SELECT name FROM categories WHERE id = c.parent_id) as parent_name
           FROM assets a
           LEFT JOIN categories c ON a.category_id = c.id
           {scope_where}
           ORDER BY c.parent_id, a.category_id, a.id DESC""",
        scope_params
    ).fetchall()
    items = []
    category_summary = {}  # 按二级分类汇总
    for a in rows:
        method = a["depreciation_method"] if "depreciation_method" in a.keys() and a["depreciation_method"] else "straight"
        accumulated = float(a["accumulated_depreciation"] or 0) if "accumulated_depreciation" in a.keys() else 0
        net = float(a["net_value"] or 0) if "net_value" in a.keys() else 0
        price = float(a["purchase_price"] or 0)
        monthly = float(a["monthly_depreciation"] or 0) if "monthly_depreciation" in a.keys() else 0
        cat_name = a["category_name"] or "未分类"
        parent_name = a["parent_name"] or ""
        items.append({
            "asset_no": a["asset_no"],
            "name": a["name"],
            "category_name": cat_name,
            "parent_name": parent_name,
            "purchase_price": price,
            "monthly_depreciation": round(monthly, 2),
            "accumulated_depreciation": round(accumulated, 2),
            "net_value": round(net, 2),
            "method": method,
            "status": "已折旧" if accumulated >= price and price > 0 else ("折旧中" if accumulated > 0 else "未折旧")
        })
        # 按二级分类汇总
        key = cat_name if not parent_name else f"{parent_name} > {cat_name}"
        if key not in category_summary:
            category_summary[key] = {"original": 0, "depreciation": 0, "net": 0, "count": 0}
        category_summary[key]["original"] += price
        category_summary[key]["depreciation"] += accumulated
        category_summary[key]["net"] += net
        category_summary[key]["count"] += 1

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        method_map = {"straight": "直线法", "once": "一次性"}
        writer.writerow(["资产编号", "名称", "分类", "原值", "月折旧额", "累计折旧", "净值", "折旧方法", "状态"])
        for item in items:
            writer.writerow([item["asset_no"], item["name"], item["category_name"],
                             item["purchase_price"], item["monthly_depreciation"],
                             item["accumulated_depreciation"], item["net_value"],
                             method_map.get(item["method"], item["method"]), item["status"]])
        # 分类汇总
        writer.writerow([])
        writer.writerow(["分类汇总", "", "", "原值合计", "累计折旧合计", "净值合计", "资产数量"])
        for cat, v in category_summary.items():
            writer.writerow([cat, "", "", round(v["original"], 2), round(v["depreciation"], 2),
                             round(v["net"], 2), v["count"]])
        output.seek(0)
        db.close()
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv; charset=utf-8",
                                 headers={"Content-Disposition": f"attachment; filename=depreciation_{suffix}.csv"})

    total_original = sum(it["purchase_price"] for it in items)
    total_depreciation = sum(it["accumulated_depreciation"] for it in items)
    total_net = sum(it["net_value"] for it in items)
    db.close()
    return Response(data={
        "items": items,
        "summary": {
            "total_original": round(total_original, 2),
            "total_depreciation": round(total_depreciation, 2),
            "total_net": round(total_net, 2)
        },
        "category_summary": [{"category": k, **v} for k, v in category_summary.items()]
    }).model_dump()
