# 报废管理路由：独立 scraps 表 CRUD
# 创建报废时校验资产存在、scrap_reason 必填、自然老化时 aging_match 必填

import io
import csv
import random
import string
from datetime import date
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from database import get_db
from auth import get_current_user, require_permission, require_dept_scope
from schemas import ScrapCreate, Response

router = APIRouter(prefix="/api/scraps", tags=["报废管理"])


def _log(db, user_id: int, desc: str):
    db.execute("INSERT INTO operation_logs (user_id, description) VALUES (?, ?)", (user_id, desc))
    db.commit()


@router.get("")
def list_scraps(
    format: str = Query(None),
    page: int = Query(1), page_size: int = Query(20),
    user: dict = Depends(require_permission("scrap:read")),
    scope: dict = Depends(require_dept_scope())
):
    db = get_db()
    conditions = []
    params = []
    if scope:
        for k, v in scope.items():
            conditions.append(f"a.{k} = ?")
            params.append(v)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    count_from = "FROM scraps s LEFT JOIN assets a ON s.asset_id = a.id" if scope else "FROM scraps s"
    total = db.execute(f"SELECT COUNT(*) {count_from} {where}", params).fetchone()[0]
    offset = (page - 1) * page_size
    rows = db.execute(
        f"""SELECT s.*, a.asset_no, a.name as asset_name
           FROM scraps s LEFT JOIN assets a ON s.asset_id = a.id
           {where}
           ORDER BY s.id DESC LIMIT ? OFFSET ?""",
        params + [page_size, offset]
    ).fetchall()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["资产编号", "资产名称", "报废原因", "年限匹配", "责任人", "报废日期", "备注", "操作人"])
        all_rows = db.execute(
            f"""SELECT s.*, a.asset_no, a.name as asset_name
               FROM scraps s LEFT JOIN assets a ON s.asset_id = a.id
               {where}
               ORDER BY s.id DESC""",
            params
        ).fetchall()
        for r in all_rows:
            writer.writerow([r["asset_no"], r["asset_name"], r["scrap_reason"],
                             "是" if r["aging_match"] else "否", r["damage_responsible"] or "",
                             r["scrap_date"], r["remark"] or "", r["operator_id"]])
        output.seek(0)
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        db.close()
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv; charset=utf-8",
                                 headers={"Content-Disposition": f"attachment; filename=scraps_{suffix}.csv"})

    db.close()
    return Response(data={"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}).model_dump()


@router.post("")
def create_scrap(req: ScrapCreate, user: dict = Depends(require_permission("scrap:create"))):
    """创建报废记录，校验资产存在、scrap_reason 必填、自然老化时 aging_match 必填"""
    if req.scrap_reason not in ("自然老化", "人为损坏"):
        return Response(code=1, message="报废原因只能为：自然老化 / 人为损坏").model_dump()
    if req.scrap_reason == "自然老化" and not req.aging_match:
        return Response(code=1, message="自然老化报废须确认 aging_match").model_dump()
    db = get_db()
    asset = db.execute("SELECT * FROM assets WHERE id = ?", (req.asset_id,)).fetchone()
    if not asset:
        db.close()
        return Response(code=1, message="资产不存在").model_dump()
    db.execute(
        """INSERT INTO scraps (asset_id, scrap_reason, aging_match, damage_responsible,
           scrap_date, remark, operator_id)
           VALUES (?,?,?,?,?,?,?)""",
        (req.asset_id, req.scrap_reason, req.aging_match,
         req.damage_responsible, req.scrap_date.isoformat() if hasattr(req.scrap_date, 'isoformat') else req.scrap_date,
         req.remark, user["id"])
    )
    db.execute("UPDATE assets SET status = 'scrapped', update_time = CURRENT_TIMESTAMP WHERE id = ?", (req.asset_id,))
    db.commit()
    sid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    _log(db, user["id"], f"报废: {asset['asset_no']} ({req.scrap_reason})")
    db.close()
    return Response(data={"id": sid}, message="报废完成").model_dump()
