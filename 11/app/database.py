from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config import DATABASE_URL, USE_SQLITE

connect_args = {"check_same_thread": False} if USE_SQLITE else {}
engine = create_async_engine(DATABASE_URL, echo=False, connect_args=connect_args)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        yield session
