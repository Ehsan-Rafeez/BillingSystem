from django.urls import path
from . import views

urlpatterns = [
    path('create_orders/', views.create_orders, name='create_orders'),
    path('list_orders/', views.list_orders, name='list_orders'),
]
