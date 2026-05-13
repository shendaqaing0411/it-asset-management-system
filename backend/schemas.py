from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


# ---- 通用 ----
class Response(BaseModel):
    code: int = 0
    data: Optional[dict | list] = None
    message: str = "ok"


class Pagination(BaseModel):
    page: int = 1
    page_size: int = 20
    total: int = 0
    items: list = []


# ---- 认证 ----
class LoginReq(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


# ---- 资产 ----
class AssetCreate(BaseModel):
    name: str = Field(..., min_length=1)
    category_id: int = Field(..., gt=0)
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_no: Optional[str] = None
    purchase_price: float = Field(default=0, ge=0)
    purchase_date: Optional[date] = None
    dept_id: Optional[int] = None
    user_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    location: Optional[str] = None
    supplier_id: Optional[int] = None
    warranty_date: Optional[date] = None
    remark: Optional[str] = None


class AssetUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    category_id: Optional[int] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_no: Optional[str] = None
    purchase_price: Optional[float] = Field(default=None, ge=0)
    purchase_date: Optional[date] = None
    dept_id: Optional[int] = None
    user_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    location: Optional[str] = None
    supplier_id: Optional[int] = None
    warranty_date: Optional[date] = None
    remark: Optional[str] = None


# ---- 库存 ----
class StockInReq(BaseModel):
    asset_id: int = Field(..., gt=0)
    type: str = "采购入库"
    quantity: int = Field(default=1, ge=1)
    to_warehouse_id: Optional[int] = None
    to_dept_id: Optional[int] = None
    to_user_id: Optional[int] = None
    remark: Optional[str] = None


class StockOutReq(BaseModel):
    asset_id: int = Field(..., gt=0)
    type: str = "领用出库"
    quantity: int = Field(default=1, ge=1)
    to_dept_id: Optional[int] = None
    to_user_id: Optional[int] = None
    remark: Optional[str] = None


class StockTransferReq(BaseModel):
    asset_id: int = Field(..., gt=0)
    to_warehouse_id: Optional[int] = None
    to_dept_id: Optional[int] = None
    to_user_id: Optional[int] = None
    remark: Optional[str] = None


# ---- 维修 ----
class RepairCreate(BaseModel):
    asset_id: int = Field(..., gt=0)
    fault_desc: Optional[str] = None
    repair_type: Optional[str] = None
    repair_cost: float = Field(default=0, ge=0)
    repair_date: Optional[date] = None


class RepairUpdate(BaseModel):
    fault_desc: Optional[str] = None
    repair_type: Optional[str] = None
    repair_cost: Optional[float] = Field(default=None, ge=0)
    finish_date: Optional[date] = None
    status: Optional[str] = None
    remark: Optional[str] = None


# ---- 报废 ----
class ScrapReq(BaseModel):
    asset_id: int = Field(..., gt=0)
    remark: Optional[str] = None


# ---- 基础数据 ----
class DeptCreate(BaseModel):
    name: str = Field(..., min_length=1)
    parent_id: int = 0
    sort_order: int = 0


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1)
    parent_id: int = 0
    sort_order: int = 0


class SupplierCreate(BaseModel):
    name: str = Field(..., min_length=1)
    contact: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    remark: Optional[str] = None


class WarehouseCreate(BaseModel):
    name: str = Field(..., min_length=1)
    location: Optional[str] = None
    manager_id: Optional[int] = None


class WarningCreate(BaseModel):
    warehouse_id: int = Field(..., gt=0)
    category_id: int = Field(..., gt=0)
    min_stock: int = Field(default=5, ge=0)
    max_stock: int = Field(default=100, ge=0)


# ---- 用户管理 ----
class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    real_name: Optional[str] = None
    role: str = "user"
    status: str = "active"


class UserUpdate(BaseModel):
    real_name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


class UserPasswordReset(BaseModel):
    password: str = Field(..., min_length=6, max_length=100)


# ---- 盘点 ----
class CheckPlan(BaseModel):
    name: str = Field(..., min_length=1)
    warehouse_id: Optional[int] = None
    category_id: Optional[int] = None
    remark: Optional[str] = None
