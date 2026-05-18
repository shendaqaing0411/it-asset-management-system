# 报表统计路由：资产汇总、库存统计、出入库报表

from fastapi import APIRouter, Depends, Query
from database import get_db
from auth import get_current_user
from schemas import Response

router = APIRouter(prefix="/api/report", tags=["报表统计"])


@router.get("/summary")
def summary(user: dict = Depends(get_current_user)):
    """资产汇总：按状态统计数量与总价值"""
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
    in_stock = db.execute("SELECT COUNT(*) FROM assets WHERE status = 'in_stock'").fetchone()[0]
    in_use = db.execute("SELECT COUNT(*) FROM assets WHERE status = 'in_use'").fetchone()[0]
    borrowed = db.execute("SELECT COUNT(*) FROM assets WHERE status = 'borrowed'").fetchone()[0]
    repairing = db.execute("SELECT COUNT(*) FROM assets WHERE status = 'repairing'").fetchone()[0]
    scrapped = db.execute("SELECT COUNT(*) FROM assets WHERE status = 'scrapped'").fetchone()[0]
    total_value = db.execute("SELECT COALESCE(SUM(purchase_price), 0) FROM assets").fetchone()[0]
    db.close()
    return Response(data={
        "total": total, "in_stock": in_stock, "in_use": in_use,
        "borrowed": borrowed, "repairing": repairing, "scrapped": scrapped,
        "total_value": total_value
    }).model_dump()


@router.get("/stock")
def stock_report(user: dict = Depends(get_current_user)):
    db = get_db()
    # 按二级类目统计（含一级类目分组信息）
    by_category = db.execute(
        """SELECT c.id, c.name, c.parent_id, COUNT(*) as count, COALESCE(SUM(a.purchase_price), 0) as value
           FROM assets a LEFT JOIN categories c ON a.category_id = c.id
           GROUP BY a.category_id ORDER BY count DESC"""
    ).fetchall()
    # 按一级类目汇总（含子分类明细）
    by_parent = db.execute(
        """SELECT p.id as parent_id, p.name as parent_name,
                  c.id as child_id, c.name as child_name,
                  COUNT(a.id) as count, COALESCE(SUM(a.purchase_price), 0) as value
           FROM categories c
           LEFT JOIN categories p ON c.parent_id = p.id
           LEFT JOIN assets a ON a.category_id = c.id
           WHERE c.parent_id > 0
           GROUP BY c.id
           ORDER BY p.sort_order, c.sort_order"""
    ).fetchall()
    by_status = db.execute(
        "SELECT status, COUNT(*) as count FROM assets GROUP BY status"
    ).fetchall()
    by_dept = db.execute(
        "SELECT d.name, COUNT(*) as count FROM assets a LEFT JOIN departments d ON a.dept_id = d.id GROUP BY a.dept_id"
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
    type: str = Query(None), user: dict = Depends(get_current_user)
):
    db = get_db()
    conditions = []
    params = []
    if start_date:
        conditions.append("operate_date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("operate_date <= ?")
        params.append(end_date)
    if type:
        conditions.append("type = ?")
        params.append(type)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    rows = db.execute(
        f"""SELECT s.*, a.asset_no, a.name as asset_name
           FROM stock_records s LEFT JOIN assets a ON s.asset_id = a.id
           {where} ORDER BY s.id DESC LIMIT 500""",
        params
    ).fetchall()
    summary = db.execute(
        f"""SELECT type, COUNT(*) as count FROM stock_records s {where} GROUP BY type""",
        params
    ).fetchall()
    db.close()
    return Response(data={
        "records": [dict(r) for r in rows],
        "summary": [dict(r) for r in summary]
    }).model_dump()
