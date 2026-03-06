"""Seed the database with enough data to trigger N+1 pain."""
import random
from models import SessionLocal, Base, engine, User, Order, LineItem, Product

Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()

    # Products
    products = []
    for i in range(50):
        p = Product(name=f"Product {i}", price=round(random.uniform(5, 200), 2))
        db.add(p)
        products.append(p)
    db.flush()

    # Users with many orders, each with many line items
    for i in range(10):
        user = User(name=f"User {i}", email=f"user{i}@example.com")
        db.add(user)
        db.flush()

        # 20 orders per user
        for j in range(20):
            order = Order(user_id=user.id, status=random.choice(["pending", "shipped", "delivered"]))
            db.add(order)
            db.flush()

            # 3-8 line items per order
            for _ in range(random.randint(3, 8)):
                li = LineItem(
                    order_id=order.id,
                    product_id=random.choice(products).id,
                    quantity=random.randint(1, 5),
                )
                db.add(li)

    db.commit()
    db.close()
    print("Seeded: 10 users, 200 orders, ~1000 line items, 50 products")


if __name__ == "__main__":
    seed()
