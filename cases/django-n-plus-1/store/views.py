from django.http import JsonResponse, Http404
from store.models import User, Order, Product


def health(request):
    return JsonResponse({"status": "ok"})


def list_users(request):
    users = User.objects.all()
    return JsonResponse([{"id": u.id, "name": u.name, "email": u.email} for u in users], safe=False)


def get_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise Http404
    return JsonResponse({"id": user.id, "name": user.name, "email": user.email})


def get_user_orders(request, user_id):
    """Deliberately has N+1: loads orders, then each order's line_items,
    then each line_item's product -- all lazily via Django ORM."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise Http404

    orders = []
    for order in user.orders.all():  # N queries for orders
        line_items = []
        for li in order.line_items.all():  # N queries per order
            line_items.append({
                "id": li.id,
                "quantity": li.quantity,
                "product": {
                    "id": li.product.id,  # N queries per line_item
                    "name": li.product.name,
                    "price": li.product.price,
                },
            })
        orders.append({"id": order.id, "status": order.status, "line_items": line_items})

    return JsonResponse({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "orders": orders,
    })


def list_orders(request):
    """Another N+1 hotspot: lists all orders with nested line_items + products."""
    orders = []
    for order in Order.objects.all():
        line_items = []
        for li in order.line_items.all():
            line_items.append({
                "id": li.id,
                "quantity": li.quantity,
                "product": {
                    "id": li.product.id,
                    "name": li.product.name,
                    "price": li.product.price,
                },
            })
        orders.append({"id": order.id, "status": order.status, "line_items": line_items})
    return JsonResponse(orders, safe=False)


def list_products(request):
    products = Product.objects.all()
    return JsonResponse([{"id": p.id, "name": p.name, "price": p.price} for p in products], safe=False)
