from fastapi import APIRouter, Depends, Query
from database import get_db
from auth import get_current_user
from auth import hash_password
from schemas import (
    DeptCreate, CategoryCreate, SupplierCreate, WarehouseCreate, WarningCreate,
    UserCreate, UserUpdate, UserPasswordReset, Response
)

router = APIRouter(prefix="/api", tags=["系统管理"])


# ---- 部门 ----
@router.get("/departments")
def list_depts(user: dict = Depends(get_current_user)):
    db = get_db()
    rows = db.execute("SELECT * FROM departments ORDER BY sort_order").fetchall()
    db.close()
    return Response(data=[dict(r) for r in rows]).model_dump()


@router.post("/departments")
def create_dept(req: DeptCreate, user: dict = Depends(get_current_user)):
    db = get_db()
    db.execute("INSERT INTO departments (name, parent_id, sort_order) VALUES (?,?,?)",
               (req.name, req.parent_id, req.sort_order))
    db.commit()
    db.close()
    return Response(message="部门已添加").model_dump()


@router.put("/departments/{dept_id}")
def update_dept(dept_id: int, req: DeptCreate, user: dict = Depends(get_current_user)):
    db = get_db()
    db.execute("UPDATE departments SET name=?, parent_id=?, sort_order=? WHERE id=?",
               (req.name, req.parent_id, req.sort_order, dept_id))
    db.commit()
    db.close()
    return Response(message="部门已更新").model_dump()


@router.delete("/departments/{dept_id}")
def delete_dept(dept_id: int, user: dict = Depends(get_current_user)):
    db = get_db()
    db.execute("DELETE FROM departments WHERE id = ?", (dept_id,))
    db.commit()
    db.close()
    return Response(message="部门已删除").model_dump()


# ---- 分类 ----
@router.get("/categories")
def list_categories(user: dict = Depends(get_current_user)):
    db = get_db()
    rows = db.execute("SELECT * FROM categories ORDER BY sort_order").fetchall()
    db.close()
    return Response(data=[dict(r) for r in rows]).model_dump()


@router.post("/categories")
def create_category(req: CategoryCreate, user: dict = Depends(get_current_user)):
    db = get_db()
    db.execute("INSERT INTO categories (name, parent_id, sort_order) VALUES (?,?,?)",
               (req.name, req.parent_id, req.sort_order))
    db.commit()
    db.close()
    return Response(message="分类已添加").model_dump()


@router.put("/categories/{cat_id}")
def update_category(cat_id: int, req: CategoryCreate, user: dict = Depends(get_current_user)):
    db = get_db()
    db.execute("UPDATE categories SET name=?, parent_id=?, sort_order=? WHERE id=?",
               (req.name, req.parent_id, req.sort_order, cat_id))
    db.commit()
    db.close()
    return Response(message="分类已更新").model_dump()


@router.delete("/categories/{cat_id}")
def delete_category(cat_id: int, user: dict = Depends(get_current_user)):
    db = get_db()
    db.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    db.commit()
    db.close()
    return Response(message="分类已删除").model_dump()


# ---- 供应商 ----
@router.get("/suppliers")
def list_suppliers(user: dict = Depends(get_current_user)):
    db = get_db()
    rows = db.execute("SELECT * FROM suppliers ORDER BY id DESC").fetchall()
    db.close()
    return Response(data=[dict(r) for r in rows]).model_dump()


@router.post("/suppliers")
def create_supplier(req: SupplierCreate, user: dict = Depends(get_current_user)):
    db = get_db()
    db.execute("INSERT INTO suppliers (name, contact, phone, address, remark) VALUES (?,?,?,?,?)",
               (req.name, req.contact, req.phone, req.address, req.remark))
    db.commit()
    db.close()
    return Response(message="供应商已添加").model_dump()


@router.put("/suppliers/{sup_id}")
def update_supplier(sup_id: int, req: SupplierCreate, user: dict = Depends(get_current_user)):
    db = get_db()
    db.execute("UPDATE suppliers SET name=?, contact=?, phone=?, address=?, remark=? WHERE id=?",
               (req.name, req.contact, req.phone, req.address, req.remark, sup_id))
    db.commit()
    db.close()
    return Response(message="供应商已更新").model_dump()


@router.delete("/suppliers/{sup_id}")
def delete_supplier(sup_id: int, user: dict = Depends(get_current_user)):
    db = get_db()
    db.execute("DELETE FROM suppliers WHERE id = ?", (sup_id,))
    db.commit()
    db.close()
    return Response(message="供应商已删除").model_dump()


# ---- 仓库 ----
@router.get("/warehouses")
def list_warehouses(user: dict = Depends(get_current_user)):
    db = get_db()
    rows = db.execute("SELECT * FROM warehouses ORDER BY id").fetchall()
    db.close()
    return Response(data=[dict(r) for r in rows]).model_dump()


@router.post("/warehouses")
def create_warehouse(req: WarehouseCreate, user: dict = Depends(get_current_user)):
    db = get_db()
    db.execute("INSERT INTO warehouses (name, location, manager_id) VALUES (?,?,?)",
               (req.name, req.location, req.manager_id))
    db.commit()
    db.close()
    return Response(message="仓库已添加").model_dump()


@router.put("/warehouses/{wh_id}")
def update_warehouse(wh_id: int, req: WarehouseCreate, user: dict = Depends(get_current_user)):
    db = get_db()
    db.execute("UPDATE warehouses SET name=?, location=?, manager_id=? WHERE id=?",
               (req.name, req.location, req.manager_id, wh_id))
    db.commit()
    db.close()
    return Response(message="仓库已更新").model_dump()


@router.delete("/warehouses/{wh_id}")
def delete_warehouse(wh_id: int, user: dict = Depends(get_current_user)):
    db = get_db()
    db.execute("DELETE FROM warehouses WHERE id = ?", (wh_id,))
    db.commit()
    db.close()
    return Response(message="仓库已删除").model_dump()


# ---- 库存预警 ----
@router.get("/warnings")
def list_warnings(user: dict = Depends(get_current_user)):
    db = get_db()
    rows = db.execute(
        """SELECT w.*, c.name as category_name, wh.name as warehouse_name
           FROM stock_warnings w
           LEFT JOIN categories c ON w.category_id = c.id
           LEFT JOIN warehouses wh ON w.warehouse_id = wh.id""",
    ).fetchall()
    db.close()
    return Response(data=[dict(r) for r in rows]).model_dump()


@router.post("/warnings")
def create_warning(req: WarningCreate, user: dict = Depends(get_current_user)):
    db = get_db()
    db.execute(
        "INSERT INTO stock_warnings (warehouse_id, category_id, min_stock, max_stock) VALUES (?,?,?,?)",
        (req.warehouse_id, req.category_id, req.min_stock, req.max_stock)
    )
    db.commit()
    db.close()
    return Response(message="预警规则已添加").model_dump()


@router.put("/warnings/{warn_id}")
def update_warning(warn_id: int, req: WarningCreate, user: dict = Depends(get_current_user)):
    db = get_db()
    db.execute(
        "UPDATE stock_warnings SET warehouse_id=?, category_id=?, min_stock=?, max_stock=? WHERE id=?",
        (req.warehouse_id, req.category_id, req.min_stock, req.max_stock, warn_id)
    )
    db.commit()
    db.close()
    return Response(message="预警规则已更新").model_dump()


@router.delete("/warnings/{warn_id}")
def delete_warning(warn_id: int, user: dict = Depends(get_current_user)):
    db = get_db()
    db.execute("DELETE FROM stock_warnings WHERE id = ?", (warn_id,))
    db.commit()
    db.close()
    return Response(message="预警规则已删除").model_dump()


# ---- 操作日志 ----
@router.get("/logs")
def list_logs(page: int = Query(1), page_size: int = Query(50), user: dict = Depends(get_current_user)):
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM operation_logs").fetchone()[0]
    offset = (page - 1) * page_size
    rows = db.execute(
        """SELECT l.*, u.username, u.real_name
           FROM operation_logs l LEFT JOIN users u ON l.user_id = u.id
           ORDER BY l.id DESC LIMIT ? OFFSET ?""",
        (page_size, offset)
    ).fetchall()
    db.close()
    return Response(data={"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}).model_dump()


# ---- 用户管理 ----
@router.get("/users")
def list_users(user: dict = Depends(get_current_user)):
    db = get_db()
    rows = db.execute("SELECT id, username, real_name, role, status, create_time FROM users ORDER BY id").fetchall()
    db.close()
    return Response(data=[dict(r) for r in rows]).model_dump()


@router.post("/users")
def create_user(req: UserCreate, user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        return Response(code=1, message="仅管理员可操作").model_dump()
    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE username = ?", (req.username,)).fetchone()
    if existing:
        db.close()
        return Response(code=1, message="用户名已存在").model_dump()
    pwd = hash_password(req.password)
    db.execute(
        "INSERT INTO users (username, password, real_name, role, status) VALUES (?,?,?,?,?)",
        (req.username, pwd, req.real_name or req.username, req.role, req.status)
    )
    db.commit()
    uid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.execute("INSERT INTO operation_logs (user_id, description) VALUES (?,?)",
               (user["id"], f"创建用户 {req.username}"))
    db.commit()
    db.close()
    return Response(data={"id": uid}, message="用户创建成功").model_dump()


@router.put("/users/{user_id}")
def update_user(user_id: int, req: UserUpdate, user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        return Response(code=1, message="仅管理员可操作").model_dump()
    db = get_db()
    existing = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not existing:
        db.close()
        return Response(code=1, message="用户不存在").model_dump()
    fields = {k: v for k, v in req.model_dump().items() if v is not None}
    if fields:
        sets = ", ".join(f"{k} = ?" for k in fields)
        db.execute(f"UPDATE users SET {sets} WHERE id = ?", list(fields.values()) + [user_id])
        db.commit()
        db.execute("INSERT INTO operation_logs (user_id, description) VALUES (?,?)",
                   (user["id"], f"更新用户 {existing['username']}"))
        db.commit()
    db.close()
    return Response(message="更新成功").model_dump()


@router.put("/users/{user_id}/password")
def reset_user_password(user_id: int, req: UserPasswordReset, user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        return Response(code=1, message="仅管理员可操作").model_dump()
    db = get_db()
    existing = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not existing:
        db.close()
        return Response(code=1, message="用户不存在").model_dump()
    pwd = hash_password(req.password)
    db.execute("UPDATE users SET password = ? WHERE id = ?", (pwd, user_id))
    db.commit()
    db.execute("INSERT INTO operation_logs (user_id, description) VALUES (?,?)",
               (user["id"], f"重置用户 {existing['username']} 的密码"))
    db.commit()
    db.close()
    return Response(message="密码重置成功").model_dump()


@router.delete("/users/{user_id}")
def delete_user(user_id: int, user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        return Response(code=1, message="仅管理员可操作").model_dump()
    if user_id == user["id"]:
        return Response(code=1, message="不能删除自己").model_dump()
    db = get_db()
    existing = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not existing:
        db.close()
        return Response(code=1, message="用户不存在").model_dump()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    db.execute("INSERT INTO operation_logs (user_id, description) VALUES (?,?)",
               (user["id"], f"删除用户 {existing['username']}"))
    db.commit()
    db.close()
    return Response(message="用户已删除").model_dump()
