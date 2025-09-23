from django.urls import path
from . import views

urlpatterns = [
    path('orders/', views.list_orders, name='list_orders'),
    path('create_order/', views.create_order, name='create_orders'),

    # Payment entry
    path('payment-entry/select/', views.payment_entry_select, name='payment_entry_select'),
    path('payment-entry/<int:order_id>/', views.payment_entry, name='payment_entry'),

    # Order actions
    path('edit_order/<int:order_id>/', views.edit_order, name='edit_order'),
    path('delete_order/<int:order_id>/', views.delete_order, name='delete_order'),
]
