from fastapi import APIRouter, Depends, Query
from database import get_db
from auth import get_current_user
from schemas import Response

router = APIRouter(prefix="/api/report", tags=["报表统计"])


@router.get("/summary")
def summary(user: dict = Depends(get_current_user)):
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
    by_category = db.execute(
        """SELECT c.name, COUNT(*) as count, COALESCE(SUM(a.purchase_price), 0) as value
           FROM assets a LEFT JOIN categories c ON a.category_id = c.id
           GROUP BY a.category_id ORDER BY count DESC"""
    ).fetchall()
    by_status = db.execute(
        "SELECT status, COUNT(*) as count FROM assets GROUP BY status"
    ).fetchall()
    by_dept = db.execute(
        "SELECT d.name, COUNT(*) as count FROM assets a LEFT JOIN departments d ON a.dept_id = d.id GROUP BY a.dept_id"
    ).fetchall()
    db.close()
    return Response(data={
        "by_category": [dict(r) for r in by_category],
        "by_status": [dict(r) for r in by_status],
        "by_dept": [dict(r) for r in by_dept]
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
