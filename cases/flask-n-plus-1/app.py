from flask import Flask, jsonify, abort
from models import db, User, Order, LineItem, Product

app = Flask(__name__)
app.config.from_object("config")
db.init_app(app)

with app.app_context():
    db.create_all()


# ── Endpoints ──


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/api/users")
def list_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])


@app.get("/api/users/<int:user_id>")
def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    return jsonify(user.to_dict())


@app.get("/api/users/<int:user_id>/orders")
def get_user_orders(user_id):
    """Deliberately has N+1: loads orders, then each order's line_items,
    then each line_item's product -- all lazily."""
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    return jsonify(user.to_dict_with_orders())


@app.get("/api/orders")
def list_orders():
    """Another N+1 hotspot: lists all orders with nested line_items + products."""
    orders = Order.query.all()
    return jsonify([o.to_dict_full() for o in orders])


@app.get("/api/products")
def list_products():
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products])
