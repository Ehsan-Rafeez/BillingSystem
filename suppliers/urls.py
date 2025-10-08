from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    # Supplier URLs
    path('', views.supplier_list, name='supplier_list'),
    path('create/', views.supplier_create, name='supplier_create'),
    path('<int:supplier_id>/', views.supplier_detail, name='supplier_detail'),
    path('<int:supplier_id>/edit/', views.supplier_edit, name='supplier_edit'),
    path('<int:supplier_id>/delete/', views.supplier_delete, name='supplier_delete'),
    path('<int:supplier_id>/payment/', views.payment_create, name='payment_create'),
    
    # Purchase Order URLs
    path('purchase-orders/', views.purchase_order_list, name='purchase_order_list'),
    path('purchase-orders/create/', views.purchase_order_create, name='purchase_order_create'),
    path('purchase-orders/<int:po_id>/', views.purchase_order_detail, name='purchase_order_detail'),
]

