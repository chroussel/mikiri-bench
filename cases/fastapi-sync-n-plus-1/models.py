from sqlalchemy import Column, Integer, String, Float, ForeignKey, create_engine
from sqlalchemy.orm import DeclarativeBase, relationship, Session, sessionmaker
import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://postgres:test@localhost:5432/test"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)

    orders = relationship("Order", back_populates="user")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, nullable=False, default="pending")

    user = relationship("User", back_populates="orders")
    line_items = relationship("LineItem", back_populates="order")


class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    order = relationship("Order", back_populates="line_items")
    product = relationship("Product")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
