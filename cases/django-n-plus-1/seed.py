"""Seed the database with enough data to trigger N+1 pain."""
import os
import random
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from store.models import User, Order, LineItem, Product


def seed():
    # Products
    products = []
    for i in range(50):
        p = Product.objects.create(name=f"Product {i}", price=round(random.uniform(5, 200), 2))
        products.append(p)

    # Users with many orders, each with many line items
    for i in range(10):
        user = User.objects.create(name=f"User {i}", email=f"user{i}@example.com")

        for j in range(20):
            order = Order.objects.create(
                user=user,
                status=random.choice(["pending", "shipped", "delivered"]),
            )

            for _ in range(random.randint(3, 8)):
                LineItem.objects.create(
                    order=order,
                    product=random.choice(products),
                    quantity=random.randint(1, 5),
                )

    print("Seeded: 10 users, 200 orders, ~1000 line items, 50 products")


if __name__ == "__main__":
    seed()
