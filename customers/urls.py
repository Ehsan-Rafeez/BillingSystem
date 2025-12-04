from django.urls import path
from . import views

urlpatterns = [
    path('customers/', views.CustomerListView.as_view(), name='list_customer'),
    path('customer/create/', views.CustomerCreateView.as_view(), name='create_customer'),
    path('customer/edit/<int:pk>/', views.CustomerUpdateView.as_view(), name='edit_customer'),
    path('customer/delete/<int:pk>/', views.CustomerDeleteView.as_view(), name='delete_customer'),
]
