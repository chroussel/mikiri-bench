"""Seed the database with enough data to trigger N+1 pain."""
import random
from app import app
from models import db, User, Order, LineItem, Product


def seed():
    with app.app_context():
        db.create_all()

        # Products
        products = []
        for i in range(50):
            p = Product(name=f"Product {i}", price=round(random.uniform(5, 200), 2))
            db.session.add(p)
            products.append(p)
        db.session.flush()

        # Users with many orders, each with many line items
        for i in range(10):
            user = User(name=f"User {i}", email=f"user{i}@example.com")
            db.session.add(user)
            db.session.flush()

            for j in range(20):
                order = Order(
                    user_id=user.id,
                    status=random.choice(["pending", "shipped", "delivered"]),
                )
                db.session.add(order)
                db.session.flush()

                for _ in range(random.randint(3, 8)):
                    li = LineItem(
                        order_id=order.id,
                        product_id=random.choice(products).id,
                        quantity=random.randint(1, 5),
                    )
                    db.session.add(li)

        db.session.commit()
        print("Seeded: 10 users, 200 orders, ~1000 line items, 50 products")


if __name__ == "__main__":
    seed()
