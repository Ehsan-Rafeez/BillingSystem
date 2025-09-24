from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.CustomerListView.as_view(), name='list_customer'),
    path('create/', views.CustomerCreateView.as_view(), name='create_customer'),
    path('edit/<int:pk>/', views.CustomerUpdateView.as_view(), name='edit_customer'),
    path('delete/<int:pk>/', views.CustomerDeleteView.as_view(), name='delete_customer'),
]
