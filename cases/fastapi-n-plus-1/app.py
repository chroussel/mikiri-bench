from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from models import AsyncSessionLocal, Base, async_engine, User, Order, LineItem, Product

app = FastAPI(title="Fixture Store API")


@app.on_event("startup")
async def on_startup():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as db:
        yield db


# ── Schemas ──


class UserOut(BaseModel):
    id: int
    name: str
    email: str

    model_config = {"from_attributes": True}


class ProductOut(BaseModel):
    id: int
    name: str
    price: float

    model_config = {"from_attributes": True}


class LineItemOut(BaseModel):
    id: int
    quantity: int
    product: ProductOut

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: int
    status: str
    line_items: list[LineItemOut]

    model_config = {"from_attributes": True}


class UserOrdersOut(BaseModel):
    id: int
    name: str
    email: str
    orders: list[OrderOut]

    model_config = {"from_attributes": True}


# ── Endpoints ──


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/users", response_model=list[UserOut])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()


@app.get("/api/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/api/users/{user_id}/orders", response_model=UserOrdersOut)
async def get_user_orders(user_id: int, db: AsyncSession = Depends(get_db)):
    """Loads user with orders, line_items, and products via selectin loading.
    The lazy='selectin' on relationships causes extra SELECT queries per relationship level."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/api/orders", response_model=list[OrderOut])
async def list_orders(db: AsyncSession = Depends(get_db)):
    """Lists all orders with nested line_items + products via selectin loading."""
    result = await db.execute(select(Order))
    return result.scalars().all()


@app.get("/api/products", response_model=list[ProductOut])
async def list_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product))
    return result.scalars().all()
