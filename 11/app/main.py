from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.database import engine, async_session
from app.models import Base, Product
from app.inventory import get_redis, init_stock_cache, close_redis
from app.order_worker import order_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        result = await session.execute(select(Product))
        products = result.scalars().all()
        if not products:
            session.add_all([
                Product(name="iPhone 16 Pro", price=0.01, total_stock=100),
                Product(name="MacBook Air M4", price=0.01, total_stock=50),
                Product(name="AirPods Pro 3", price=0.01, total_stock=200),
            ])
            await session.commit()
            result = await session.execute(select(Product))
            products = result.scalars().all()

        for p in products:
            await init_stock_cache(p.id, p.total_stock)

    order_worker.start()
    yield
    order_worker.stop()
    await close_redis()


app = FastAPI(title="秒杀系统", lifespan=lifespan)

static_dir = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

from app.routers import auth, products, seckill
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(seckill.router)


@app.get("/")
async def index():
    return FileResponse(static_dir / "index.html")


@app.get("/login")
async def login_page():
    return FileResponse(static_dir / "login.html")
