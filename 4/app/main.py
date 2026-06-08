from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.services.cache_service import init_redis, close_redis
from app.routers import auth, short_link, stats, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    await init_redis()
    yield
    await close_redis()


app = FastAPI(
    title="ShortLink Service",
    description="Enhanced short link service with auth, stats, and caching",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(short_link.router)
app.include_router(stats.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    return {"message": "ShortLink Service API", "docs": "/docs"}
