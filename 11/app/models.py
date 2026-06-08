from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    total_stock = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    product_id = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
