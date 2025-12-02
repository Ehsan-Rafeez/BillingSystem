from django.urls import path
from . import views

urlpatterns = [
    path("", views.expense_list, name="expense_list"),
    path("create/", views.expense_create, name="expense_create"),
    path("<int:pk>/edit/", views.expense_update, name="expense_update"),
    path("<int:pk>/delete/", views.expense_delete, name="expense_delete"),
    path("reports/expenses/", views.expense_report, name="expense_report"),
    path("categories/", views.expense_category_list, name="expense_category_list"),
    path("categories/create/", views.expense_category_create, name="expense_category_create"),
    path("categories/<int:pk>/edit/", views.expense_category_update, name="expense_category_update"),
]
