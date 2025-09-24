# inventory/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.add_stock, name='add_stock'),  # 'add_stock' route
    path('list/', views.list_stock, name='list_stock'),  # 'list_stock' route
]
