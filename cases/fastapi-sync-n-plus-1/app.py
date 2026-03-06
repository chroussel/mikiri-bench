from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from models import SessionLocal, Base, engine, User, Order, LineItem, Product

app = FastAPI(title="Fixture Store API")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
def health():
    return {"status": "ok"}


@app.get("/api/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@app.get("/api/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/api/users/{user_id}/orders", response_model=UserOrdersOut)
def get_user_orders(user_id: int, db: Session = Depends(get_db)):
    """Deliberately has N+1: loads orders, then each order's line_items,
    then each line_item's product — all lazily."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Access orders (lazy load → 1 query)
    # Access each order's line_items (lazy load → N queries)
    # Access each line_item's product (lazy load → N queries)
    return user


@app.get("/api/orders", response_model=list[OrderOut])
def list_orders(db: Session = Depends(get_db)):
    """Another N+1 hotspot: lists all orders with nested line_items + products."""
    return db.query(Order).all()


@app.get("/api/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()
