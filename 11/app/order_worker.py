import asyncio
from sqlalchemy import select
from app.database import async_session
from app.models import Order
from app.inventory import incr_stock, get_redis


class OrderWorker:
    def __init__(self):
        self.queue: asyncio.Queue | None = None
        self._task: asyncio.Task | None = None

    def start(self):
        self.queue = asyncio.Queue()
        self._task = asyncio.create_task(self._process_loop())

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def enqueue(self, order_id: str, user_id: int, product_id: int):
        await self.queue.put({
            "order_id": order_id,
            "user_id": user_id,
            "product_id": product_id,
        })

    async def _process_loop(self):
        while True:
            item = await self.queue.get()
            try:
                await self._process_order(item)
            except Exception:
                await self._rollback_order(item)
            finally:
                self.queue.task_done()

    async def _process_order(self, item: dict):
        async with async_session() as session:
            async with session.begin():
                order = Order(
                    id=item["order_id"],
                    user_id=item["user_id"],
                    product_id=item["product_id"],
                    status="success",
                )
                session.add(order)
                await session.commit()

        r = await get_redis()
        await r.set(f"order_result:{item['order_id']}", "success", ex=300)

    async def _rollback_order(self, item: dict):
        await incr_stock(item["product_id"])
        r = await get_redis()
        await r.set(f"order_result:{item['order_id']}", "failed", ex=300)
        try:
            async with async_session() as session:
                async with session.begin():
                    result = await session.execute(
                        select(Order).where(Order.id == item["order_id"])
                    )
                    order = result.scalar_one_or_none()
                    if order:
                        order.status = "failed"
                        await session.commit()
        except Exception:
            pass


order_worker = OrderWorker()
