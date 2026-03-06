from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship, Session, sessionmaker
from sqlalchemy import create_engine
import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://postgres:test@localhost:5432/test"
)

# Async engine for the FastAPI app (asyncpg driver)
ASYNC_DATABASE_URL = DATABASE_URL.replace("+psycopg", "+asyncpg").replace(
    "postgresql://", "postgresql+asyncpg://"
)
async_engine = create_async_engine(ASYNC_DATABASE_URL, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

# Sync engine for seeding and table creation
sync_engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)

    orders = relationship("Order", back_populates="user", lazy="selectin")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, nullable=False, default="pending")

    user = relationship("User", back_populates="orders")
    line_items = relationship("LineItem", back_populates="order", lazy="selectin")


class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    order = relationship("Order", back_populates="line_items")
    product = relationship("Product", lazy="selectin")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
