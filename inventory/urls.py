from django.urls import path
from . import views

urlpatterns = [
    path("add/", views.add_stock, name="add_stock"),
    path("list/", views.list_stock, name="list_stock"),
    path("add_inventory/", views.add_inventory, name="add_inventory"),
    path("list_inventory/", views.list_inventory, name="list_inventory"),
    path("live_stock/", views.live_stock, name="live_stock"),

    # 🔹 New Routes
    path("edit/<int:pk>/", views.edit_stock, name="edit_stock"),
    path("delete/<int:pk>/", views.delete_stock, name="delete_stock"),
    path("payment/<int:pk>/", views.add_payment, name="add_payment"),
    path("restock/<int:pk>/", views.restock_item, name="restock_item"),

    # Inventory Base Items (catalog)
    path("baseitems/", views.base_item_list, name="baseitem_list"),
    path("baseitems/create/", views.base_item_create, name="baseitem_create"),
    path("baseitems/<int:pk>/edit/", views.base_item_update, name="baseitem_update"),
    path("baseitems/<int:pk>/delete/", views.base_item_delete, name="baseitem_delete"),

    # Units and Categories management
    path("units/", views.uom_list, name="uom_list"),
    path("units/create/", views.uom_create, name="uom_create"),
    path("units/<int:pk>/edit/", views.uom_update, name="uom_update"),

    path("categories/", views.category_list, name="inventory_category_list"),
    path("categories/create/", views.category_create, name="inventory_category_create"),
    path("categories/<int:pk>/edit/", views.category_update, name="inventory_category_update"),

    # Reports
    path("reports/purchases/", views.stock_purchase_report, name="stock_purchase_report"),
    path("reports/usage/", views.stock_usage_report, name="stock_usage_report"),
]
