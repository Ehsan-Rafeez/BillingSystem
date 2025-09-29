from django.urls import path
from . import views

urlpatterns = [
    path("add/", views.add_stock, name="add_stock"),
    path("list/", views.list_stock, name="list_stock"),
    path("<int:pk>/edit/", views.edit_stock, name="edit_stock"),
    path("<int:pk>/delete/", views.delete_stock, name="delete_stock"),
    path("<int:pk>/returned/", views.mark_returned, name="mark_returned"),
]
