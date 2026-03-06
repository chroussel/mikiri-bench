from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)

    orders = db.relationship("Order", back_populates="user", lazy="select")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email}

    def to_dict_with_orders(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "orders": [o.to_dict_full() for o in self.orders],
        }


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String, nullable=False, default="pending")

    user = db.relationship("User", back_populates="orders")
    line_items = db.relationship("LineItem", back_populates="order", lazy="select")

    def to_dict(self):
        return {"id": self.id, "status": self.status}

    def to_dict_full(self):
        return {
            "id": self.id,
            "status": self.status,
            "line_items": [li.to_dict() for li in self.line_items],
        }


class LineItem(db.Model):
    __tablename__ = "line_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    order = db.relationship("Order", back_populates="line_items")
    product = db.relationship("Product", lazy="select")

    def to_dict(self):
        return {
            "id": self.id,
            "quantity": self.quantity,
            "product": self.product.to_dict(),
        }


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "price": self.price}
