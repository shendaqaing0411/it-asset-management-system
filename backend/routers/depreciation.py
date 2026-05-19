# 折旧配置管理：按分类自定义折旧方法和年限
from fastapi import APIRouter, Depends
from database import get_db
from auth import get_current_user, require_permission
from schemas import Response
from pydantic import BaseModel, Field
from typing import Optional, Literal

router = APIRouter(prefix="/api/depreciation-configs", tags=["折旧配置"])


class DepreciationConfigReq(BaseModel):
    category_id: int
    method: Literal["straight", "once"] = "straight"
    useful_life_years: int = Field(default=5, gt=0)
    salvage_rate: float = Field(default=0, ge=0, le=1)


@router.get("")
def list_configs(user: dict = Depends(get_current_user)):
    db = get_db()
    rows = db.execute(
        """SELECT dc.*, c.name as category_name,
                  (SELECT name FROM categories WHERE id = c.parent_id) as parent_name
           FROM depreciation_configs dc
           LEFT JOIN categories c ON dc.category_id = c.id
           ORDER BY c.parent_id, dc.category_id"""
    ).fetchall()
    db.close()
    return Response(data=[dict(r) for r in rows]).model_dump()


@router.post("")
def save_config(body: DepreciationConfigReq, user: dict = Depends(require_permission("depreciation:config"))):
    db = get_db()
    # 校验分类存在
    cat = db.execute("SELECT id FROM categories WHERE id = ?", (body.category_id,)).fetchone()
    if not cat:
        db.close()
        return Response(code=1, message="分类不存在").model_dump()
    existing = db.execute(
        "SELECT id FROM depreciation_configs WHERE category_id = ?", (body.category_id,)
    ).fetchone()
    if existing:
        db.execute(
            """UPDATE depreciation_configs
               SET method=?, useful_life_years=?, salvage_rate=?, update_time=CURRENT_TIMESTAMP
               WHERE id=?""",
            (body.method, body.useful_life_years, body.salvage_rate, existing["id"])
        )
    else:
        db.execute(
            """INSERT INTO depreciation_configs (category_id, method, useful_life_years, salvage_rate)
               VALUES (?, ?, ?, ?)""",
            (body.category_id, body.method, body.useful_life_years, body.salvage_rate)
        )
    db.commit()
    db.close()
    return Response(message="保存成功").model_dump()


@router.delete("/{config_id}")
def delete_config(config_id: int, user: dict = Depends(require_permission("depreciation:config"))):
    db = get_db()
    cur = db.execute("DELETE FROM depreciation_configs WHERE id = ?", (config_id,))
    if cur.rowcount == 0:
        db.close()
        return Response(code=1, message="配置不存在").model_dump()
    db.commit()
    db.close()
    return Response(message="删除成功").model_dump()
