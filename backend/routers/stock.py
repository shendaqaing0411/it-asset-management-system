# 库存管理路由：出入库、归还、调拨、库存查询、预警监测
# 出入库同时更新 assets 表状态与 stock_records 表记录

import io
import csv
import random
import string
from datetime import date
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from database import get_db
from auth import get_current_user
from schemas import StockInReq, StockOutReq, StockTransferReq, CheckReq, Response

router = APIRouter(prefix="/api/stock", tags=["库存管理"])


def _log(db, user_id: int, desc: str):
    db.execute("INSERT INTO operation_logs (user_id, description) VALUES (?, ?)", (user_id, desc))
    db.commit()


def _asset_row(db, asset_id: int):
    return db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()


@router.get("/query")
def query_stock(
    keyword: str = Query(None), category_id: int = Query(None),
    parent_category_id: int = Query(None),
    status: str = Query(None), warehouse_id: int = Query(None),
    page: int = Query(1), page_size: int = Query(20),
    user: dict = Depends(get_current_user)
):
    db = get_db()
    conditions = []
    params = []
    if keyword:
        conditions.append("(a.name LIKE ? OR a.asset_no LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    if category_id:
        conditions.append("a.category_id = ?")
        params.append(category_id)
    if parent_category_id:
        conditions.append("c.parent_id = ?")
        params.append(parent_category_id)
    if status:
        conditions.append("a.status = ?")
        params.append(status)
    if warehouse_id:
        conditions.append("a.warehouse_id = ?")
        params.append(warehouse_id)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    count_from = "FROM assets a LEFT JOIN categories c ON a.category_id = c.id" if parent_category_id else "FROM assets a"
    total = db.execute(f"SELECT COUNT(*) {count_from} {where}", params).fetchone()[0]
    offset = (page - 1) * page_size
    rows = db.execute(
        f"""SELECT a.*, c.name as category_name, w.name as warehouse_name
           FROM assets a
           LEFT JOIN categories c ON a.category_id = c.id
           LEFT JOIN warehouses w ON a.warehouse_id = w.id
           {where} ORDER BY a.id DESC LIMIT ? OFFSET ?""",
        params + [page_size, offset]
    ).fetchall()
    items = [dict(r) for r in rows]
    db.close()
    return Response(data={"total": total, "page": page, "page_size": page_size, "items": items}).model_dump()


@router.post("/in")
def stock_in(req: StockInReq, user: dict = Depends(get_current_user)):
    db = get_db()
    asset = _asset_row(db, req.asset_id)
    if not asset:
        db.close()
        return Response(code=1, message="资产不存在").model_dump()
    today = date.today().isoformat()
    db.execute(
        """INSERT INTO stock_records (asset_id, type, quantity, to_warehouse_id, to_dept_id,
           to_user_id, operator_id, operate_date, remark)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (req.asset_id, req.type, req.quantity, req.to_warehouse_id, req.to_dept_id,
         req.to_user_id, user["id"], today, req.remark)
    )
    db.execute("UPDATE assets SET status = 'in_stock', update_time = CURRENT_TIMESTAMP WHERE id = ?",
               (req.asset_id,))
    db.commit()
    _log(db, user["id"], f"入库: {asset['asset_no']} ({req.type})")
    db.close()
    return Response(message="入库成功").model_dump()


@router.post("/out")
def stock_out(req: StockOutReq, user: dict = Depends(get_current_user)):
    db = get_db()
    asset = _asset_row(db, req.asset_id)
    if not asset:
        db.close()
        return Response(code=1, message="资产不存在").model_dump()
    today = date.today().isoformat()
    new_status = "borrowed" if req.type == "借用出库" else "in_use"
    db.execute(
        """INSERT INTO stock_records (asset_id, type, quantity, to_dept_id, to_user_id,
           operator_id, operate_date, remark)
           VALUES (?,?,?,?,?,?,?,?)""",
        (req.asset_id, req.type, req.quantity, req.to_dept_id, req.to_user_id, user["id"], today, req.remark)
    )
    db.execute("UPDATE assets SET status = ?, dept_id = ?, user_id = ?, update_time = CURRENT_TIMESTAMP WHERE id = ?",
               (new_status, req.to_dept_id or asset["dept_id"], req.to_user_id or asset["user_id"], req.asset_id))
    db.commit()
    _log(db, user["id"], f"出库: {asset['asset_no']} ({req.type})")
    db.close()
    return Response(message="出库成功").model_dump()


@router.post("/return/{asset_id}")
def return_asset(asset_id: int, user: dict = Depends(get_current_user)):
    db = get_db()
    asset = _asset_row(db, asset_id)
    if not asset:
        db.close()
        return Response(code=1, message="资产不存在").model_dump()
    if asset["status"] not in ("borrowed", "in_use"):
        db.close()
        return Response(code=1, message="该资产当前未借出").model_dump()
    today = date.today().isoformat()
    db.execute(
        """INSERT INTO stock_records (asset_id, type, quantity, operator_id, operate_date, remark)
           VALUES (?,?,?,?,?,?)""",
        (asset_id, "归还", 1, user["id"], today, "归还入库")
    )
    db.execute("UPDATE assets SET status = 'in_stock', dept_id = NULL, user_id = NULL, update_time = CURRENT_TIMESTAMP WHERE id = ?",
               (asset_id,))
    db.commit()
    _log(db, user["id"], f"归还: {asset['asset_no']}")
    db.close()
    return Response(message="归还成功").model_dump()


@router.post("/transfer")
def transfer(req: StockTransferReq, user: dict = Depends(get_current_user)):
    db = get_db()
    asset = _asset_row(db, req.asset_id)
    if not asset:
        db.close()
        return Response(code=1, message="资产不存在").model_dump()
    today = date.today().isoformat()
    db.execute(
        """INSERT INTO stock_records (asset_id, type, quantity, from_warehouse_id, to_warehouse_id,
           from_dept_id, to_dept_id, operator_id, operate_date, remark)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (req.asset_id, "调拨", 1, asset["warehouse_id"], req.to_warehouse_id,
         asset["dept_id"], req.to_dept_id, user["id"], today, req.remark)
    )
    updates = ["update_time = CURRENT_TIMESTAMP"]
    params = []
    if req.to_warehouse_id is not None:
        updates.append("warehouse_id = ?")
        params.append(req.to_warehouse_id)
    if req.to_dept_id is not None:
        updates.append("dept_id = ?")
        params.append(req.to_dept_id)
    if req.to_user_id is not None:
        updates.append("user_id = ?")
        params.append(req.to_user_id)
    db.execute(f"UPDATE assets SET {', '.join(updates)} WHERE id = ?", params + [req.asset_id])
    db.commit()
    _log(db, user["id"], f"调拨: {asset['asset_no']}")
    db.close()
    return Response(message="调拨成功").model_dump()


@router.get("/records")
def stock_records(
    asset_id: int = Query(None), type: str = Query(None),
    format: str = Query(None),
    page: int = Query(1), page_size: int = Query(20),
    user: dict = Depends(get_current_user)
):
    db = get_db()
    conditions = []
    params = []
    if asset_id:
        conditions.append("s.asset_id = ?")
        params.append(asset_id)
    if type:
        conditions.append("s.type = ?")
        params.append(type)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    if format == "csv":
        all_rows = db.execute(
            f"""SELECT s.*, a.asset_no, a.name as asset_name
               FROM stock_records s LEFT JOIN assets a ON s.asset_id = a.id
               {where} ORDER BY s.id DESC""",
            params
        ).fetchall()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["资产编号", "资产名称", "操作类型", "数量", "来源/去向部门", "操作人", "操作日期", "备注"])
        for r in all_rows:
            writer.writerow([r["asset_no"], r["asset_name"], r["type"], r["quantity"],
                             r["to_dept_id"] or "", r["operator_id"], r["operate_date"], r["remark"] or ""])
        output.seek(0)
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        db.close()
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv; charset=utf-8",
                                 headers={"Content-Disposition": f"attachment; filename=stock_records_{suffix}.csv"})

    total = db.execute(f"SELECT COUNT(*) FROM stock_records s {where}", params).fetchone()[0]
    offset = (page - 1) * page_size
    rows = db.execute(
        f"""SELECT s.*, a.asset_no, a.name as asset_name
           FROM stock_records s LEFT JOIN assets a ON s.asset_id = a.id
           {where} ORDER BY s.id DESC LIMIT ? OFFSET ?""",
        params + [page_size, offset]
    ).fetchall()
    db.close()
    return Response(data={"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}).model_dump()


@router.get("/warnings")
def get_warnings(user: dict = Depends(get_current_user)):
    """获取库存预警：对比当前库存与预警阈值，返回低库存/高库存告警"""
    db = get_db()
    rows = db.execute(
        """SELECT w.*, c.name as category_name, wh.name as warehouse_name,
           (SELECT COUNT(*) FROM assets a WHERE a.category_id = w.category_id AND a.warehouse_id = w.warehouse_id AND a.status = 'in_stock') as current_stock
           FROM stock_warnings w
           LEFT JOIN categories c ON w.category_id = c.id
           LEFT JOIN warehouses wh ON w.warehouse_id = wh.id""",
    ).fetchall()
    result = []
    for r in rows:
        item = dict(r)
        item["warning"] = None
        if item["current_stock"] < item["min_stock"]:
            item["warning"] = "low"
        elif item["current_stock"] > item["max_stock"]:
            item["warning"] = "high"
        result.append(item)
    db.close()
    return Response(data=result).model_dump()


@router.post("/check")
def stock_check(req: CheckReq, user: dict = Depends(get_current_user)):
    """盘点确认：接收盘点结果数组，盘盈→入库记录，盘亏→出库记录"""
    db = get_db()
    today = date.today().isoformat()
    surplus_count = 0
    loss_count = 0
    for item in req.items:
        asset_id = item.get("asset_id")
        result = item.get("result")
        remark = item.get("remark", "")
        asset = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not asset:
            continue
        if result == "surplus":
            db.execute(
                """INSERT INTO stock_records (asset_id, type, quantity, operator_id, operate_date, remark)
                   VALUES (?,?,?,?,?,?)""",
                (asset_id, "盘盈入库", 1, user["id"], today, remark)
            )
            db.execute("UPDATE assets SET status='in_stock', update_time=CURRENT_TIMESTAMP WHERE id=?", (asset_id,))
            surplus_count += 1
        elif result == "loss":
            db.execute(
                """INSERT INTO stock_records (asset_id, type, quantity, operator_id, operate_date, remark)
                   VALUES (?,?,?,?,?,?)""",
                (asset_id, "盘亏出库", 1, user["id"], today, remark)
            )
            db.execute("UPDATE assets SET status='scrapped', update_time=CURRENT_TIMESTAMP WHERE id=?", (asset_id,))
            loss_count += 1
    db.commit()
    _log(db, user["id"], f"盘点确认: 盘盈 {surplus_count} 条, 盘亏 {loss_count} 条")
    db.close()
    return Response(data={"surplus": surplus_count, "loss": loss_count}, message="盘点完成").model_dump()
