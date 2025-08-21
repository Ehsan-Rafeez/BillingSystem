from django.urls import path, include

from .views import customers_index, CustomerListView,CustomerCreateView,CustomerIndexView,CustomerUpdateView, CustomerDeleteView
urlpatterns = [
    path('', CustomerIndexView.as_view(), name='customer_index'),  # Home page view

    # Add more customer-related URLs here as needed
    path('list/', CustomerListView.as_view(), name='customer_list'),
    path('create/', CustomerCreateView.as_view(), name='create_customer'),
    path('edit/<int:pk>/', CustomerUpdateView.as_view(), name='edit_customer'),
    path('delete/<int:pk>/', CustomerDeleteView.as_view(), name='delete_customer'),
]
