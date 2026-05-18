# 领用审批路由：提交申请、列表查询（按角色过滤）、审批、确认出库

import io
import csv
import random
import string
from datetime import date
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from database import get_db
from auth import get_current_user
from schemas import ApprovalCreate, ApprovalApprove, Response

router = APIRouter(prefix="/api/approvals", tags=["领用审批"])


def _log(db, user_id: int, desc: str):
    db.execute("INSERT INTO operation_logs (user_id, description) VALUES (?, ?)", (user_id, desc))
    db.commit()


@router.get("")
def list_approvals(
    status: str = Query(None),
    format: str = Query(None),
    page: int = Query(1), page_size: int = Query(20),
    user: dict = Depends(get_current_user)
):
    """按角色过滤：普通用户看自己的，主管看本部门的，管理员看全部"""
    db = get_db()
    conditions = []
    params = []
    if status:
        conditions.append("ap.status = ?")
        params.append(status)
    # 角色过滤
    if user["role"] in ("user", "dept_manager"):
        if user["role"] == "user":
            conditions.append("ap.applicant_id = ?")
            params.append(user["id"])
        elif user["role"] == "dept_manager":
            conditions.append("ap.dept_id = ?")
            params.append(user.get("dept_id", 0))
    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    if format == "csv":
        all_rows = db.execute(
            f"""SELECT ap.*, a.asset_no, a.name as asset_name,
                       u1.real_name as applicant_name, u2.real_name as approver_name,
                       d.name as dept_name
                FROM approvals ap
                LEFT JOIN assets a ON ap.asset_id = a.id
                LEFT JOIN users u1 ON ap.applicant_id = u1.id
                LEFT JOIN users u2 ON ap.approver_id = u2.id
                LEFT JOIN departments d ON ap.dept_id = d.id
                {where} ORDER BY ap.id DESC""",
            params
        ).fetchall()
        output = io.StringIO()
        writer = csv.writer(output)
        status_map = {"pending": "待审批", "approved": "已通过", "rejected": "已拒绝", "delivered": "已出库"}
        writer.writerow(["资产编号", "资产名称", "申请人", "申请部门", "申请原因", "申请日期", "状态", "审批人", "审批日期", "出库日期"])
        for r in all_rows:
            writer.writerow([r["asset_no"], r["asset_name"], r["applicant_name"] or "", r["dept_name"] or "",
                             r["apply_reason"] or "", r["apply_date"], status_map.get(r["status"], r["status"]),
                             r["approver_name"] or "", r["approve_date"] or "", r["deliver_date"] or ""])
        output.seek(0)
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        db.close()
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv; charset=utf-8",
                                 headers={"Content-Disposition": f"attachment; filename=approvals_{suffix}.csv"})

    total = db.execute(f"SELECT COUNT(*) FROM approvals ap {where}", params).fetchone()[0]
    offset = (page - 1) * page_size
    rows = db.execute(
        f"""SELECT ap.*, a.asset_no, a.name as asset_name,
                   u1.real_name as applicant_name, u2.real_name as approver_name,
                   d.name as dept_name
            FROM approvals ap
            LEFT JOIN assets a ON ap.asset_id = a.id
            LEFT JOIN users u1 ON ap.applicant_id = u1.id
            LEFT JOIN users u2 ON ap.approver_id = u2.id
            LEFT JOIN departments d ON ap.dept_id = d.id
            {where} ORDER BY ap.id DESC LIMIT ? OFFSET ?""",
        params + [page_size, offset]
    ).fetchall()
    db.close()
    return Response(data={"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}).model_dump()


@router.post("")
def create_approval(req: ApprovalCreate, user: dict = Depends(get_current_user)):
    """提交领用申请（仅 user/dept_manager 可调用）"""
    if user["role"] not in ("user", "dept_manager"):
        return Response(code=1, message="仅普通用户/部门主管可提交领用申请").model_dump()
    db = get_db()
    asset = db.execute("SELECT * FROM assets WHERE id = ?", (req.asset_id,)).fetchone()
    if not asset:
        db.close()
        return Response(code=1, message="资产不存在").model_dump()
    today = date.today().isoformat()
    db.execute(
        """INSERT INTO approvals (asset_id, applicant_id, dept_id, apply_reason, apply_date)
           VALUES (?,?,?,?,?)""",
        (req.asset_id, user["id"], req.dept_id, req.apply_reason, today)
    )
    db.commit()
    aid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    _log(db, user["id"], f"提交领用申请: {asset['asset_no']}")
    # 通知资产管理员
    admins = db.execute("SELECT id FROM users WHERE role IN ('super_admin','asset_admin')").fetchall()
    for a in admins:
        db.execute(
            "INSERT INTO notifications (user_id, type, title, content, ref_id) VALUES (?,?,?,?,?)",
            (a["id"], "approval_pending", "新的领用申请",
             f"{user['real_name']} 申请领用 {asset['asset_no']} {asset['name']}", aid)
        )
    db.commit()
    db.close()
    return Response(data={"id": aid}, message="申请已提交").model_dump()


@router.put("/{approval_id}/approve")
def approve(approval_id: int, req: ApprovalApprove, user: dict = Depends(get_current_user)):
    """审批：dept_manager 只能审批本部门申请，admin/asset_admin 不受限"""
    db = get_db()
    ap = db.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
    if not ap:
        db.close()
        return Response(code=1, message="审批记录不存在").model_dump()
    if ap["status"] != "pending":
        db.close()
        return Response(code=1, message="该申请已处理").model_dump()
    if user["role"] == "dept_manager" and ap["dept_id"] != user.get("dept_id"):
        db.close()
        return Response(code=1, message="只能审批本部门的申请").model_dump()
    if user["role"] not in ("super_admin", "asset_admin", "dept_manager"):
        db.close()
        return Response(code=1, message="无审批权限").model_dump()
    status = "approved" if req.approved else "rejected"
    today = date.today().isoformat()
    db.execute(
        "UPDATE approvals SET status=?, approver_id=?, reject_reason=?, approve_date=? WHERE id=?",
        (status, user["id"], req.reject_reason if not req.approved else None, today, approval_id)
    )
    db.commit()
    # 通知申请人
    db.execute(
        "INSERT INTO notifications (user_id, type, title, content, ref_id) VALUES (?,?,?,?,?)",
        (ap["applicant_id"], "approval_pending",
         "领用申请已审批",
         f"您的领用申请已被{'通过' if req.approved else '驳回'}" + (f"：{req.reject_reason}" if not req.approved else ""),
         approval_id)
    )
    db.commit()
    _log(db, user["id"], f"审批领用申请 #{approval_id}: {status}")
    db.close()
    return Response(message="审批完成").model_dump()


@router.put("/{approval_id}/deliver")
def deliver(approval_id: int, user: dict = Depends(get_current_user)):
    """确认出库（admin/asset_admin），写 stock_record，更新资产状态"""
    if user["role"] not in ("super_admin", "asset_admin"):
        return Response(code=1, message="仅管理员/资产管理员可确认出库").model_dump()
    db = get_db()
    ap = db.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
    if not ap:
        db.close()
        return Response(code=1, message="审批记录不存在").model_dump()
    if ap["status"] != "approved":
        db.close()
        return Response(code=1, message="仅已审批的申请可出库").model_dump()
    today = date.today().isoformat()
    db.execute(
        """INSERT INTO stock_records (asset_id, type, quantity, to_dept_id, to_user_id,
           operator_id, operate_date, remark)
           VALUES (?,?,?,?,?,?,?,?)""",
        (ap["asset_id"], "领用出库", 1, ap["dept_id"], ap["applicant_id"],
         user["id"], today, f"审批领用 #{approval_id}")
    )
    db.execute("UPDATE assets SET status='in_use', dept_id=?, user_id=?, update_time=CURRENT_TIMESTAMP WHERE id=?",
               (ap["dept_id"], ap["applicant_id"], ap["asset_id"]))
    db.execute("UPDATE approvals SET status='delivered', deliver_date=? WHERE id=?",
               (today, approval_id))
    db.commit()
    asset = db.execute("SELECT asset_no FROM assets WHERE id = ?", (ap["asset_id"],)).fetchone()
    _log(db, user["id"], f"确认出库: {asset['asset_no']} (审批 #{approval_id})")
    db.close()
    return Response(message="出库完成").model_dump()
