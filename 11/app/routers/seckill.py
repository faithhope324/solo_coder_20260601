import uuid
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Order as OrderModel
from app.models import Product as ProductModel
from app.inventory import decr_stock, incr_stock, get_redis, get_stock
from app.rate_limiter import check_rate_limit
from app.order_worker import order_worker
from app.schemas import ApiResponse

router = APIRouter(prefix="/api/seckill", tags=["seckill"])


@router.post("/{product_id}")
async def seckill(
    product_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await check_rate_limit(user["id"], product_id):
        return ApiResponse(code=429, message="请求过快，每秒只能抢一次")

    result = await db.execute(select(ProductModel).where(ProductModel.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        return ApiResponse(code=404, message="商品不存在")

    remaining = await decr_stock(product_id)
    if remaining < 0:
        await incr_stock(product_id)
        return ApiResponse(code=0, message="已售罄", data={"remaining_stock": 0})

    order_id = str(uuid.uuid4())
    r = await get_redis()
    await r.set(f"order_result:{order_id}", "pending", ex=300)

    await order_worker.enqueue(order_id, user["id"], product_id)

    current_stock = await get_stock(product_id)
    return ApiResponse(
        code=0,
        message="抢购排队中",
        data={"order_id": order_id, "remaining_stock": max(current_stock, 0)},
    )


@router.get("/result/{order_id}")
async def seckill_result(
    order_id: str,
    user: dict = Depends(get_current_user),
):
    r = await get_redis()
    status_val = await r.get(f"order_result:{order_id}")
    if status_val is None:
        return ApiResponse(code=0, data={"status": "unknown"}, message="订单不存在或已过期")

    product_name = None
    if status_val == "success":
        from app.database import async_session
        from app.models import Order, Product
        async with async_session() as session:
            result = await session.execute(
                select(Order, Product.name)
                .join(Product, Order.product_id == Product.id)
                .where(Order.id == order_id)
            )
            row = result.first()
            if row:
                product_name = row[1]

    return ApiResponse(
        code=0,
        data={"status": status_val, "product_name": product_name},
        message="ok",
    )
