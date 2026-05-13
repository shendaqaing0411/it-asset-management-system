# 维保报废路由：维修记录管理、资产报废
# 维修完成后自动将资产状态恢复为"在库"
# 报废通过 stock_records 表 type='报废' 记录

from datetime import date
from fastapi import APIRouter, Depends, Query
from database import get_db
from auth import get_current_user
from schemas import RepairCreate, RepairUpdate, ScrapReq, Response

router = APIRouter(prefix="/api", tags=["维保报废"])


def _log(db, user_id: int, desc: str):
    db.execute("INSERT INTO operation_logs (user_id, description) VALUES (?, ?)", (user_id, desc))
    db.commit()


@router.get("/repairs")
def list_repairs(page: int = Query(1), page_size: int = Query(20), user: dict = Depends(get_current_user)):
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM repairs").fetchone()[0]
    offset = (page - 1) * page_size
    rows = db.execute(
        """SELECT r.*, a.asset_no, a.name as asset_name
           FROM repairs r LEFT JOIN assets a ON r.asset_id = a.id
           ORDER BY r.id DESC LIMIT ? OFFSET ?""",
        (page_size, offset)
    ).fetchall()
    db.close()
    return Response(data={"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}).model_dump()


@router.post("/repairs")
def create_repair(req: RepairCreate, user: dict = Depends(get_current_user)):
    """创建维修记录，同时将资产状态更新为"维修中" """
    db = get_db()
    db.execute(
        """INSERT INTO repairs (asset_id, fault_desc, repair_type, repair_cost, repair_date)
           VALUES (?,?,?,?,?)""",
        (req.asset_id, req.fault_desc, req.repair_type, req.repair_cost, req.repair_date)
    )
    db.execute("UPDATE assets SET status = 'repairing', update_time = CURRENT_TIMESTAMP WHERE id = ?", (req.asset_id,))
    db.commit()
    rid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    _log(db, user["id"], f"新增维修记录: 资产ID {req.asset_id}")
    db.close()
    return Response(data={"id": rid}, message="维修记录已创建").model_dump()


@router.put("/repairs/{repair_id}")
def update_repair(repair_id: int, req: RepairUpdate, user: dict = Depends(get_current_user)):
    db = get_db()
    existing = db.execute("SELECT * FROM repairs WHERE id = ?", (repair_id,)).fetchone()
    if not existing:
        db.close()
        return Response(code=1, message="维修记录不存在").model_dump()
    fields = {k: v for k, v in req.model_dump().items() if v is not None}
    if fields:
        sets = ", ".join(f"{k} = ?" for k in fields)
        vals = list(fields.values()) + [repair_id]
        db.execute(f"UPDATE repairs SET {sets} WHERE id = ?", vals)
        if fields.get("status") == "finished":
            db.execute("UPDATE assets SET status = 'in_stock', update_time = CURRENT_TIMESTAMP WHERE id = ?",
                       (existing["asset_id"],))
        db.commit()
        _log(db, user["id"], f"更新维修记录 #{repair_id}")
    db.close()
    return Response(message="更新成功").model_dump()


# 报废（简化，直接记录）
@router.get("/scraps")
def list_scraps(page: int = Query(1), page_size: int = Query(20), user: dict = Depends(get_current_user)):
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM stock_records WHERE type = '报废'").fetchone()[0]
    offset = (page - 1) * page_size
    rows = db.execute(
        """SELECT s.*, a.asset_no, a.name as asset_name
           FROM stock_records s LEFT JOIN assets a ON s.asset_id = a.id
           WHERE s.type = '报废' ORDER BY s.id DESC LIMIT ? OFFSET ?""",
        (page_size, offset)
    ).fetchall()
    db.close()
    return Response(data={"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}).model_dump()


@router.post("/scraps")
def scrap_asset(req: ScrapReq, user: dict = Depends(get_current_user)):
    db = get_db()
    asset = db.execute("SELECT * FROM assets WHERE id = ?", (req.asset_id,)).fetchone()
    if not asset:
        db.close()
        return Response(code=1, message="资产不存在").model_dump()
    today = date.today().isoformat()
    db.execute(
        "INSERT INTO stock_records (asset_id, type, quantity, operator_id, operate_date, remark) VALUES (?,?,?,?,?,?)",
        (req.asset_id, "报废", 1, user["id"], today, req.remark)
    )
    db.execute("UPDATE assets SET status = 'scrapped', update_time = CURRENT_TIMESTAMP WHERE id = ?", (req.asset_id,))
    db.commit()
    _log(db, user["id"], f"报废: {asset['asset_no']}")
    db.close()
    return Response(message="报废完成").model_dump()
