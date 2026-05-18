# 维保报废路由：维修记录管理、报废管理（已迁移至 scraps.py）
# repair_type 校验枚举值：保修期内维修/保外维修/厂商送修/自行维修
# 维修完成 ≠ 返修入库，只有 POST /api/repairs/{id}/return 才恢复资产状态

import io
import csv
import random
import string
from datetime import date
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from database import get_db
from auth import get_current_user
from schemas import RepairCreate, RepairUpdate, RepairReturnReq, Response

router = APIRouter(prefix="/api", tags=["维保报废"])

VALID_REPAIR_TYPES = {"保修期内维修", "保外维修", "厂商送修", "自行维修"}


def _log(db, user_id: int, desc: str):
    db.execute("INSERT INTO operation_logs (user_id, description) VALUES (?, ?)", (user_id, desc))
    db.commit()


@router.get("/repairs")
def list_repairs(format: str = Query(None), page: int = Query(1), page_size: int = Query(20), user: dict = Depends(get_current_user)):
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM repairs").fetchone()[0]
    offset = (page - 1) * page_size
    rows = db.execute(
        """SELECT r.*, a.asset_no, a.name as asset_name
           FROM repairs r LEFT JOIN assets a ON r.asset_id = a.id
           ORDER BY r.id DESC LIMIT ? OFFSET ?""",
        (page_size, offset)
    ).fetchall()

    if format == "csv":
        all_rows = db.execute(
            """SELECT r.*, a.asset_no, a.name as asset_name
               FROM repairs r LEFT JOIN assets a ON r.asset_id = a.id
               ORDER BY r.id DESC"""
        ).fetchall()
        output = io.StringIO()
        writer = csv.writer(output)
        status_map = {"pending": "待处理", "fixing": "维修中", "finished": "已完成"}
        writer.writerow(["资产编号", "资产名称", "维修类型", "维修方式", "故障描述", "维修状态", "送修日期", "完成日期", "返修日期", "返修确认", "费用"])
        for r in all_rows:
            writer.writerow([r["asset_no"], r["asset_name"], r["repair_type"] or "", r["repair_method"] or "",
                             r["fault_desc"] or "", status_map.get(r["status"], r["status"]),
                             r["repair_date"] or "", r["finish_date"] or "",
                             r["return_date"] or "", "是" if r["return_confirmed"] else "否", r["repair_cost"] or ""])
        output.seek(0)
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        db.close()
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv; charset=utf-8",
                                 headers={"Content-Disposition": f"attachment; filename=repairs_{suffix}.csv"})

    db.close()
    return Response(data={"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}).model_dump()


@router.post("/repairs")
def create_repair(req: RepairCreate, user: dict = Depends(get_current_user)):
    """创建维修记录，同时将资产状态更新为"维修中" """
    if req.repair_type and req.repair_type not in VALID_REPAIR_TYPES:
        return Response(code=1, message=f"维修类型只能为：{'/'.join(VALID_REPAIR_TYPES)}").model_dump()
    db = get_db()
    asset = db.execute("SELECT id FROM assets WHERE id = ?", (req.asset_id,)).fetchone()
    if not asset:
        db.close()
        return Response(code=1, message="资产不存在").model_dump()
    db.execute(
        """INSERT INTO repairs (asset_id, fault_desc, repair_type, repair_method, repair_cost, repair_date)
           VALUES (?,?,?,?,?,?)""",
        (req.asset_id, req.fault_desc, req.repair_type, req.repair_method, req.repair_cost, req.repair_date)
    )
    db.execute("UPDATE assets SET status = 'repairing', update_time = CURRENT_TIMESTAMP WHERE id = ?", (req.asset_id,))
    db.commit()
    rid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    _log(db, user["id"], f"新增维修记录: 资产ID {req.asset_id}")
    db.close()
    return Response(data={"id": rid}, message="维修记录已创建").model_dump()


@router.put("/repairs/{repair_id}")
def update_repair(repair_id: int, req: RepairUpdate, user: dict = Depends(get_current_user)):
    """更新维修记录。status='finished' 仅标记维修完成，不再自动改资产状态"""
    if req.repair_type and req.repair_type not in VALID_REPAIR_TYPES:
        return Response(code=1, message=f"维修类型只能为：{'/'.join(VALID_REPAIR_TYPES)}").model_dump()
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
    db.commit()
    _log(db, user["id"], f"更新维修记录 #{repair_id}")
    # 维修完成时生成通知给资产管理员
    if req.status == "finished":
        admins = db.execute("SELECT id FROM users WHERE role IN ('super_admin','asset_admin')").fetchall()
        asset = db.execute("SELECT asset_no, name FROM assets WHERE id = ?", (existing["asset_id"],)).fetchone()
        for a in admins:
            db.execute(
                "INSERT INTO notifications (user_id, type, title, content, ref_id) VALUES (?,?,?,?,?)",
                (a["id"], "repair_complete", "维修已完成",
                 f"资产 {asset['asset_no']} {asset['name']} 维修已完成，等待返修入库确认", repair_id)
            )
        db.commit()
    db.close()
    return Response(message="更新成功").model_dump()


@router.post("/repairs/{repair_id}/return")
def repair_return(repair_id: int, req: RepairReturnReq, user: dict = Depends(get_current_user)):
    """返修入库确认：更新 repairs.return_confirmed=1，assets.status='in_stock'"""
    db = get_db()
    existing = db.execute("SELECT * FROM repairs WHERE id = ?", (repair_id,)).fetchone()
    if not existing:
        db.close()
        return Response(code=1, message="维修记录不存在").model_dump()
    db.execute(
        "UPDATE repairs SET return_confirmed=1, return_date=? WHERE id=?",
        (req.return_date.isoformat() if hasattr(req.return_date, 'isoformat') else req.return_date, repair_id)
    )
    db.execute("UPDATE assets SET status='in_stock', update_time=CURRENT_TIMESTAMP WHERE id=?", (existing["asset_id"],))
    db.commit()
    _log(db, user["id"], f"返修入库确认: 维修记录 #{repair_id}")
    db.close()
    return Response(message="返修入库确认完成").model_dump()
