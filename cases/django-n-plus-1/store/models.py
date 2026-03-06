from django.db import models


class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)

    class Meta:
        db_table = "users"


class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.FloatField()

    class Meta:
        db_table = "products"


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=50, default="pending")

    class Meta:
        db_table = "orders"


class LineItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="line_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    class Meta:
        db_table = "line_items"
