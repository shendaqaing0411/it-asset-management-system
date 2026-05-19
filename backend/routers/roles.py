# 角色管理路由：角色 CRUD、权限码列表
# 权限码预定义，按模块分组；内置角色 is_system=1 不可删除

import json
from fastapi import APIRouter, Depends
from database import get_db
from auth import get_current_user, require_permission
from schemas import Response
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter(prefix="/api", tags=["角色管理"])

# 预定义所有合法权限码集合，用于验证
VALID_PERMISSION_CODES = set()

PERMISSION_GROUPS = [
    ("仪表盘", [
        ("dashboard:view", "查看全局统计"),
    ]),
    ("资产管理", [
        ("asset:read", "查看资产列表"),
        ("asset:create", "登记资产"),
        ("asset:update", "编辑资产"),
        ("asset:delete", "删除资产"),
        ("asset:import", "批量导入"),
        ("asset:export", "导出数据"),
    ]),
    ("库存管理", [
        ("stock:query", "库存查询"),
        ("stock:in", "入库"),
        ("stock:out", "出库"),
        ("stock:return", "归还"),
        ("stock:transfer", "调拨"),
        ("stock:check", "盘点"),
        ("stock:warning", "库存预警"),
    ]),
    ("维保管理", [
        ("repair:read", "查看维修记录"),
        ("repair:create", "登记维修"),
        ("repair:update", "编辑维修"),
        ("repair:return", "返修入库确认"),
    ]),
    ("报废管理", [
        ("scrap:read", "查看报废记录"),
        ("scrap:create", "登记报废"),
    ]),
    ("审批流", [
        ("approval:submit", "提交领用申请"),
        ("approval:approve", "审批申请"),
        ("approval:deliver", "确认出库"),
    ]),
    ("报表统计", [
        ("report:summary", "资产汇总"),
        ("report:stock", "库存统计"),
        ("report:inout", "出入库报表"),
        ("report:depreciation", "折旧报表"),
    ]),
    ("系统管理", [
        ("system:user", "用户管理"),
        ("system:role", "角色管理"),
        ("system:dept", "部门管理"),
        ("system:category", "分类管理"),
        ("system:warehouse", "仓库管理"),
        ("system:supplier", "供应商管理"),
        ("system:log", "操作日志"),
        ("system:dict", "数据字典"),
    ]),
    ("折旧", [
        ("depreciation:config", "折旧配置"),
        ("depreciation:calculate", "执行折旧计算"),
    ]),
    ("通知", [
        ("notification:view", "查看通知"),
    ]),
]

# 构建合法权限码集合，用于创建/更新角色时校验
for _module, _items in PERMISSION_GROUPS:
    for _code, _label in _items:
        VALID_PERMISSION_CODES.add(_code)


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    scope: str = "all"
    permissions: list = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    scope: Optional[str] = None
    permissions: Optional[list] = None


@router.get("/permissions")
def list_permissions(user: dict = Depends(get_current_user)):
    """返回所有权限码列表，按模块分组，供前端勾选"""
    data = []
    for module, items in PERMISSION_GROUPS:
        data.append({
            "module": module,
            "items": [{"code": code, "label": label} for code, label in items]
        })
    return Response(data=data).model_dump()


@router.get("/roles")
def list_roles(user: dict = Depends(require_permission("system:role"))):
    db = get_db()
    rows = db.execute("SELECT * FROM roles ORDER BY is_system DESC, id ASC").fetchall()
    items = []
    for r in rows:
        item = dict(r)
        item["permissions"] = json.loads(r["permissions"] or "[]")
        item["user_count"] = db.execute(
            "SELECT COUNT(*) FROM users WHERE role_id = ?", (r["id"],)
        ).fetchone()[0]
        items.append(item)
    db.close()
    return Response(data=items).model_dump()


@router.get("/roles/{role_id}")
def get_role(role_id: int, user: dict = Depends(require_permission("system:role"))):
    db = get_db()
    row = db.execute("SELECT * FROM roles WHERE id = ?", (role_id,)).fetchone()
    db.close()
    if not row:
        return Response(code=1, message="角色不存在").model_dump()
    item = dict(row)
    item["permissions"] = json.loads(row["permissions"] or "[]")
    return Response(data=item).model_dump()


@router.post("/roles")
def create_role(body: RoleCreate, user: dict = Depends(require_permission("system:role"))):
    # 校验权限码合法性
    invalid = [p for p in body.permissions if p not in VALID_PERMISSION_CODES]
    if invalid:
        return Response(code=1, message=f"无效权限码: {', '.join(invalid)}").model_dump()
    db = get_db()
    existing = db.execute("SELECT id FROM roles WHERE name = ?", (body.name,)).fetchone()
    if existing:
        db.close()
        return Response(code=1, message="角色名称已存在").model_dump()
    db.execute(
        "INSERT INTO roles (name, description, scope, permissions) VALUES (?,?,?,?)",
        (body.name, body.description, body.scope, json.dumps(body.permissions, ensure_ascii=False))
    )
    db.commit()
    rid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return Response(data={"id": rid}, message="角色创建成功").model_dump()


@router.put("/roles/{role_id}")
def update_role(role_id: int, body: RoleUpdate, user: dict = Depends(require_permission("system:role"))):
    db = get_db()
    existing = db.execute("SELECT * FROM roles WHERE id = ?", (role_id,)).fetchone()
    if not existing:
        db.close()
        return Response(code=1, message="角色不存在").model_dump()
    if existing["is_system"]:
        db.close()
        return Response(code=1, message="内置角色不可修改，请创建自定义角色").model_dump()
    # 校验权限码合法性
    if body.permissions is not None:
        invalid = [p for p in body.permissions if p not in VALID_PERMISSION_CODES]
        if invalid:
            db.close()
            return Response(code=1, message=f"无效权限码: {', '.join(invalid)}").model_dump()
    fields = {}
    if body.name is not None:
        dup = db.execute("SELECT id FROM roles WHERE name = ? AND id != ?", (body.name, role_id)).fetchone()
        if dup:
            db.close()
            return Response(code=1, message="角色名称已存在").model_dump()
        fields["name"] = body.name
    if body.description is not None:
        fields["description"] = body.description
    if body.scope is not None:
        fields["scope"] = body.scope
    if body.permissions is not None:
        fields["permissions"] = json.dumps(body.permissions, ensure_ascii=False)
    if fields:
        fields["update_time"] = "CURRENT_TIMESTAMP"
        sets = ", ".join(f"{k} = ?" for k in fields)
        db.execute(f"UPDATE roles SET {sets} WHERE id = ?", list(fields.values()) + [role_id])
        db.commit()
    db.close()
    return Response(message="角色已更新").model_dump()


@router.delete("/roles/{role_id}")
def delete_role(role_id: int, user: dict = Depends(require_permission("system:role"))):
    db = get_db()
    existing = db.execute("SELECT * FROM roles WHERE id = ?", (role_id,)).fetchone()
    if not existing:
        db.close()
        return Response(code=1, message="角色不存在").model_dump()
    if existing["is_system"]:
        db.close()
        return Response(code=1, message="内置角色不可删除").model_dump()
    user_count = db.execute("SELECT COUNT(*) FROM users WHERE role_id = ?", (role_id,)).fetchone()[0]
    if user_count > 0:
        db.close()
        return Response(code=1, message=f"该角色下有 {user_count} 个用户，请先转移用户再删除").model_dump()
    db.execute("DELETE FROM roles WHERE id = ?", (role_id,))
    db.commit()
    db.close()
    return Response(message="角色已删除").model_dump()
