from django.urls import path
from store import views

urlpatterns = [
    path("health", views.health),
    path("api/users", views.list_users),
    path("api/users/<int:user_id>", views.get_user),
    path("api/users/<int:user_id>/orders", views.get_user_orders),
    path("api/orders", views.list_orders),
    path("api/products", views.list_products),
]
