from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import User as UserModel
from app.models import Order as OrderModel
from app.models import Product as ProductModel
from app.inventory import get_stock
from app.schemas import ApiResponse

router = APIRouter(prefix="/api", tags=["products"])


@router.get("/products")
async def list_products(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    result = await db.execute(select(ProductModel))
    products = result.scalars().all()
    items = []
    for p in products:
        remaining = await get_stock(p.id)
        items.append({
            "id": p.id,
            "name": p.name,
            "price": float(p.price),
            "total_stock": p.total_stock,
            "remaining_stock": max(remaining, 0),
        })
    return ApiResponse(code=0, data=items, message="ok")


@router.get("/orders")
async def list_orders(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(OrderModel, ProductModel.name)
        .join(ProductModel, OrderModel.product_id == ProductModel.id)
        .where(OrderModel.user_id == user["id"])
        .where(OrderModel.status == "success")
        .order_by(OrderModel.created_at.desc())
    )
    rows = result.all()
    items = []
    for order, product_name in rows:
        items.append({
            "id": order.id,
            "product_id": order.product_id,
            "product_name": product_name,
            "status": order.status,
            "created_at": order.created_at.isoformat() if order.created_at else "",
        })
    return ApiResponse(code=0, data=items, message="ok")
