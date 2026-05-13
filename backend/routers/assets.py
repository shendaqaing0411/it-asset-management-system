import io
from datetime import datetime
from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from database import get_db
from auth import get_current_user
from schemas import AssetCreate, AssetUpdate, Response
import qrcode
import openpyxl

router = APIRouter(prefix="/api/assets", tags=["资产管理"])


def _format_asset(row):
    return {
        "id": row["id"], "asset_no": row["asset_no"], "name": row["name"],
        "category_id": row["category_id"], "brand": row["brand"], "model": row["model"],
        "serial_no": row["serial_no"], "purchase_price": row["purchase_price"],
        "purchase_date": row["purchase_date"], "status": row["status"],
        "dept_id": row["dept_id"], "user_id": row["user_id"],
        "warehouse_id": row["warehouse_id"], "location": row["location"],
        "supplier_id": row["supplier_id"], "warranty_date": row["warranty_date"],
        "remark": row["remark"], "create_time": row["create_time"], "update_time": row["update_time"]
    }


def _gen_asset_no(db) -> str:
    now = datetime.now()
    ym = now.strftime("%Y%m")
    row = db.execute(
        "SELECT asset_no FROM assets WHERE asset_no LIKE ? ORDER BY id DESC LIMIT 1",
        (f"IT-{ym}-%",)
    ).fetchone()
    if row:
        seq = int(row["asset_no"].split("-")[-1]) + 1
    else:
        seq = 1
    return f"IT-{ym}-{seq:04d}"


def _log(db, user_id: int, desc: str):
    db.execute("INSERT INTO operation_logs (user_id, description) VALUES (?, ?)", (user_id, desc))
    db.commit()


@router.get("")
def list_assets(
    keyword: str = Query(None), category_id: int = Query(None),
    status: str = Query(None), dept_id: int = Query(None), warehouse_id: int = Query(None),
    page: int = Query(1), page_size: int = Query(20),
    user: dict = Depends(get_current_user)
):
    db = get_db()
    conditions = []
    params = []
    if keyword:
        conditions.append("(a.name LIKE ? OR a.asset_no LIKE ? OR a.serial_no LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
    if category_id:
        conditions.append("a.category_id = ?")
        params.append(category_id)
    if status:
        conditions.append("a.status = ?")
        params.append(status)
    if dept_id:
        conditions.append("a.dept_id = ?")
        params.append(dept_id)
    if warehouse_id:
        conditions.append("a.warehouse_id = ?")
        params.append(warehouse_id)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    total = db.execute(f"SELECT COUNT(*) FROM assets a {where}", params).fetchone()[0]
    offset = (page - 1) * page_size
    rows = db.execute(
        f"""SELECT a.*, c.name as category_name, d.name as dept_name, w.name as warehouse_name
           FROM assets a
           LEFT JOIN categories c ON a.category_id = c.id
           LEFT JOIN departments d ON a.dept_id = d.id
           LEFT JOIN warehouses w ON a.warehouse_id = w.id
           {where} ORDER BY a.id DESC LIMIT ? OFFSET ?""",
        params + [page_size, offset]
    ).fetchall()
    items = []
    for r in rows:
        item = _format_asset(r)
        item["category_name"] = r["category_name"]
        item["dept_name"] = r["dept_name"]
        item["warehouse_name"] = r["warehouse_name"]
        items.append(item)
    db.close()
    return Response(data={"total": total, "page": page, "page_size": page_size, "items": items}).model_dump()


@router.get("/{asset_id}")
def get_asset(asset_id: int, user: dict = Depends(get_current_user)):
    db = get_db()
    row = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
    db.close()
    if not row:
        return Response(code=1, message="资产不存在").model_dump()
    return Response(data=_format_asset(row)).model_dump()


@router.post("")
def create_asset(req: AssetCreate, user: dict = Depends(get_current_user)):
    db = get_db()
    asset_no = _gen_asset_no(db)
    db.execute(
        """INSERT INTO assets (asset_no, name, category_id, brand, model, serial_no,
           purchase_price, purchase_date, dept_id, user_id, warehouse_id, location,
           supplier_id, warranty_date, remark)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (asset_no, req.name, req.category_id, req.brand, req.model, req.serial_no,
         req.purchase_price, req.purchase_date, req.dept_id, req.user_id,
         req.warehouse_id, req.location, req.supplier_id, req.warranty_date, req.remark)
    )
    db.commit()
    asset_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    _log(db, user["id"], f"新增资产 {asset_no} - {req.name}")
    db.close()
    return Response(data={"id": asset_id, "asset_no": asset_no}, message="资产登记成功").model_dump()


@router.put("/{asset_id}")
def update_asset(asset_id: int, req: AssetUpdate, user: dict = Depends(get_current_user)):
    db = get_db()
    existing = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
    if not existing:
        db.close()
        return Response(code=1, message="资产不存在").model_dump()
    fields = {k: v for k, v in req.model_dump().items() if v is not None}
    if fields:
        fields["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sets = ", ".join(f"{k} = ?" for k in fields)
        vals = list(fields.values()) + [asset_id]
        db.execute(f"UPDATE assets SET {sets} WHERE id = ?", vals)
        db.commit()
        _log(db, user["id"], f"更新资产 {existing['asset_no']}")
    db.close()
    return Response(message="更新成功").model_dump()


@router.delete("/{asset_id}")
def delete_asset(asset_id: int, user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        return Response(code=1, message="仅管理员可删除资产").model_dump()
    db = get_db()
    existing = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
    if not existing:
        db.close()
        return Response(code=1, message="资产不存在").model_dump()
    record_count = db.execute("SELECT COUNT(*) FROM stock_records WHERE asset_id = ?", (asset_id,)).fetchone()[0]
    repair_count = db.execute("SELECT COUNT(*) FROM repairs WHERE asset_id = ?", (asset_id,)).fetchone()[0]
    if record_count > 0 or repair_count > 0:
        db.close()
        return Response(code=1, message=f"该资产有 {record_count} 条出入库记录和 {repair_count} 条维修记录，请先清理相关记录再删除").model_dump()
    _log(db, user["id"], f"删除资产 {existing['asset_no']} - {existing['name']}")
    db.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
    db.commit()
    db.close()
    return Response(message="删除成功").model_dump()


@router.get("/qrcode/{asset_id}")
def get_qrcode(asset_id: int):
    db = get_db()
    row = db.execute("SELECT asset_no FROM assets WHERE id = ?", (asset_id,)).fetchone()
    db.close()
    if not row:
        return Response(code=1, message="资产不存在").model_dump()
    img = qrcode.make(row["asset_no"])
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@router.post("/import")
def import_assets(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    db = get_db()
    wb = openpyxl.load_workbook(file.file)
    ws = wb.active
    imported = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        asset_no = _gen_asset_no(db)
        db.execute(
            """INSERT INTO assets (asset_no, name, category_id, brand, model, serial_no,
               purchase_price, purchase_date, status)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (asset_no, row[0] or "", int(row[1] or 0), row[2] or "", row[3] or "",
             row[4] or "", float(row[5] or 0), str(row[6] or "") or None, "in_stock")
        )
        imported += 1
    db.commit()
    _log(db, user["id"], f"批量导入资产 {imported} 条")
    db.close()
    return Response(data={"count": imported}, message=f"导入成功 {imported} 条").model_dump()


@router.get("/export/all")
def export_assets(user: dict = Depends(get_current_user)):
    db = get_db()
    rows = db.execute("SELECT * FROM assets ORDER BY id DESC").fetchall()
    db.close()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "资产列表"
    headers = ["资产编号", "名称", "品牌", "型号", "序列号", "采购价格", "采购日期", "状态", "存放位置", "备注"]
    ws.append(headers)
    for r in rows:
        ws.append([r["asset_no"], r["name"], r["brand"], r["model"], r["serial_no"],
                   r["purchase_price"], r["purchase_date"], r["status"], r["location"], r["remark"]])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment; filename=assets.xlsx"})
