import os

USE_SQLITE = not os.getenv("DATABASE_URL")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./seckill.db",
)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
USE_FAKEREDIS = os.getenv("USE_FAKEREDIS", "1")
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60
