# 报废管理路由：独立 scraps 表 CRUD
# 创建报废时校验资产存在、scrap_reason 必填、自然老化时 aging_match 必填

from datetime import date
from fastapi import APIRouter, Depends, Query
from database import get_db
from auth import get_current_user
from schemas import ScrapCreate, Response

router = APIRouter(prefix="/api/scraps", tags=["报废管理"])


def _log(db, user_id: int, desc: str):
    db.execute("INSERT INTO operation_logs (user_id, description) VALUES (?, ?)", (user_id, desc))
    db.commit()


@router.get("")
def list_scraps(
    page: int = Query(1), page_size: int = Query(20),
    user: dict = Depends(get_current_user)
):
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM scraps").fetchone()[0]
    offset = (page - 1) * page_size
    rows = db.execute(
        """SELECT s.*, a.asset_no, a.name as asset_name
           FROM scraps s LEFT JOIN assets a ON s.asset_id = a.id
           ORDER BY s.id DESC LIMIT ? OFFSET ?""",
        (page_size, offset)
    ).fetchall()
    db.close()
    return Response(data={"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}).model_dump()


@router.post("")
def create_scrap(req: ScrapCreate, user: dict = Depends(get_current_user)):
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
