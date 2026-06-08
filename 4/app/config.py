from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./shortlink.db"
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    USE_REDIS: bool = False
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"
    BASE_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"


settings = Settings()
