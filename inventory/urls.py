from django.urls import path
from . import views

urlpatterns = [
    path("add/", views.add_stock, name="add_stock"),
    path("list/", views.list_stock, name="list_stock"),

    # 🔹 New Routes
    path("edit/<int:pk>/", views.edit_stock, name="edit_stock"),
    path("delete/<int:pk>/", views.delete_stock, name="delete_stock"),
    path("payment/<int:pk>/", views.add_payment, name="add_payment"),
]
