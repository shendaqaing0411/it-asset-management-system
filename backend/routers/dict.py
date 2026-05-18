from fastapi import APIRouter, Depends, Query
from database import get_db
from auth import get_current_user, require_role
from schemas import Response
from pydantic import BaseModel, Field
from typing import Optional
import json

router = APIRouter(prefix="/api/dict", tags=["数据字典"])


class DictFieldCreate(BaseModel):
    module: str = Field(..., min_length=1)
    field_key: str = Field(..., min_length=1)
    field_name: str = Field(..., min_length=1)
    field_type: str = "text"
    sort_order: int = 0
    is_required: int = 0
    options: Optional[str] = None


class DictFieldUpdate(BaseModel):
    field_name: Optional[str] = None
    field_type: Optional[str] = None
    sort_order: Optional[int] = None
    is_required: Optional[int] = None
    options: Optional[str] = None


class DictValuesSave(BaseModel):
    record_id: int = Field(..., gt=0)
    module: str = Field(..., min_length=1)
    values: dict = Field(default_factory=dict)


# ---- 字典字段 CRUD ----

@router.get("/fields")
def list_fields(module: Optional[str] = Query(None), user: dict = Depends(get_current_user)):
    db = get_db()
    if module:
        rows = db.execute(
            "SELECT * FROM dict_fields WHERE module = ? ORDER BY sort_order",
            (module,)
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM dict_fields ORDER BY module, sort_order").fetchall()
    db.close()
    return Response(data=[dict(r) for r in rows]).model_dump()


@router.post("/fields")
def create_field(req: DictFieldCreate, user: dict = Depends(require_role("super_admin", "asset_admin"))):
    db = get_db()
    existing = db.execute(
        "SELECT id FROM dict_fields WHERE module = ? AND field_key = ?",
        (req.module, req.field_key)
    ).fetchone()
    if existing:
        db.close()
        return Response(code=1, message="该模块下字段标识已存在").model_dump()
    db.execute(
        """INSERT INTO dict_fields (module, field_key, field_name, field_type, sort_order, is_required, options)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (req.module, req.field_key, req.field_name, req.field_type,
         req.sort_order, req.is_required, req.options)
    )
    db.commit()
    fid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return Response(data={"id": fid}, message="字段已添加").model_dump()


@router.put("/fields/{field_id}")
def update_field(field_id: int, req: DictFieldUpdate, user: dict = Depends(require_role("super_admin", "asset_admin"))):
    db = get_db()
    existing = db.execute("SELECT * FROM dict_fields WHERE id = ?", (field_id,)).fetchone()
    if not existing:
        db.close()
        return Response(code=1, message="字段不存在").model_dump()
    fields = {k: v for k, v in req.model_dump().items() if v is not None}
    if fields:
        sets = ", ".join(f"{k} = ?" for k in fields)
        db.execute(f"UPDATE dict_fields SET {sets} WHERE id = ?", list(fields.values()) + [field_id])
        db.commit()
    db.close()
    return Response(message="字段已更新").model_dump()


@router.delete("/fields/{field_id}")
def delete_field(field_id: int, user: dict = Depends(require_role("super_admin", "asset_admin"))):
    db = get_db()
    db.execute("DELETE FROM dict_fields WHERE id = ?", (field_id,))
    db.commit()
    db.close()
    return Response(message="字段已删除").model_dump()


# ---- 字典值存取 ----

@router.get("/values")
def get_values(module: str = Query(...), record_id: int = Query(...), user: dict = Depends(get_current_user)):
    """获取指定记录的所有字典字段值"""
    db = get_db()
    rows = db.execute(
        """SELECT df.field_key, df.field_name, df.field_type, dv.value
           FROM dict_fields df
           LEFT JOIN dict_values dv ON df.id = dv.field_id AND dv.record_id = ?
           WHERE df.module = ?
           ORDER BY df.sort_order""",
        (record_id, module)
    ).fetchall()
    db.close()
    result = {}
    for r in rows:
        result[r["field_key"]] = {
            "field_name": r["field_name"],
            "field_type": r["field_type"],
            "value": r["value"]
        }
    return Response(data=result).model_dump()


@router.post("/values")
def save_values(req: DictValuesSave, user: dict = Depends(get_current_user)):
    """保存字典值（upsert）"""
    db = get_db()
    fields = db.execute(
        "SELECT id, field_key FROM dict_fields WHERE module = ?",
        (req.module,)
    ).fetchall()
    field_map = {f["field_key"]: f["id"] for f in fields}
    for key, val in req.values.items():
        if key in field_map:
            db.execute(
                "INSERT OR REPLACE INTO dict_values (field_id, record_id, value) VALUES (?, ?, ?)",
                (field_map[key], req.record_id, str(val) if val is not None else None)
            )
    db.commit()
    db.close()
    return Response(message="字典值已保存").model_dump()
