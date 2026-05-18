# 通知中心路由：获取通知列表、未读数、标记已读

from fastapi import APIRouter, Depends, Query
from database import get_db
from auth import get_current_user
from schemas import Response

router = APIRouter(prefix="/api/notifications", tags=["通知中心"])


@router.get("")
def list_notifications(
    unread: int = Query(None),
    page: int = Query(1), page_size: int = Query(20),
    user: dict = Depends(get_current_user)
):
    db = get_db()
    conditions = ["user_id = ?"]
    params = [user["id"]]
    if unread:
        conditions.append("is_read = 0")
    where = "WHERE " + " AND ".join(conditions)
    total = db.execute(f"SELECT COUNT(*) FROM notifications {where}", params).fetchone()[0]
    offset = (page - 1) * page_size
    rows = db.execute(
        f"SELECT * FROM notifications {where} ORDER BY id DESC LIMIT ? OFFSET ?",
        params + [page_size, offset]
    ).fetchall()
    db.close()
    return Response(data={"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}).model_dump()


@router.get("/count")
def unread_count(user: dict = Depends(get_current_user)):
    db = get_db()
    count = db.execute(
        "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0",
        (user["id"],)
    ).fetchone()[0]
    db.close()
    return Response(data={"count": count}).model_dump()


@router.put("/{notification_id}/read")
def mark_read(notification_id: int, user: dict = Depends(get_current_user)):
    db = get_db()
    row = db.execute(
        "SELECT * FROM notifications WHERE id = ? AND user_id = ?",
        (notification_id, user["id"])
    ).fetchone()
    if not row:
        db.close()
        return Response(code=1, message="通知不存在").model_dump()
    db.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
    db.commit()
    db.close()
    return Response(message="已标记已读").model_dump()
