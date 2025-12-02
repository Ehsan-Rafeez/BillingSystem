from django.urls import path
from . import views

urlpatterns = [
    # Events / Bookings
    path('events/', views.event_list, name='list_events'),
    path('events/create/', views.event_create, name='create_event'),
    path('events/<int:event_id>/edit/', views.event_update, name='edit_event'),

    # Menus
    path('menus/', views.menu_list, name='menu_list'),
    path('menus/create/', views.menu_create, name='menu_create'),
    path('menus/<int:item_id>/edit/', views.menu_update, name='menu_update'),
    path('menus/categories/', views.category_list, name='category_list'),
    path('menus/categories/create/', views.category_create, name='category_create'),
    path('menus/categories/<int:category_id>/edit/', views.category_update, name='category_update'),

    # Quotes / Proposals
    path('quotes/', views.quote_list, name='quote_list'),
    path('quotes/create/', views.quote_create, name='quote_create'),
    path('quotes/<int:quote_id>/edit/', views.quote_update, name='quote_update'),
    path('quotes/<int:quote_id>/', views.quote_detail, name='quote_detail'),

    # Reports
    path('reports/revenue/', views.revenue_report, name='revenue_report'),
    path('reports/pnl/', views.profit_loss_report, name='profit_loss_report'),

    path('orders/', views.list_orders, name='list_orders'),
    path('create_order/', views.create_order, name='create_orders'),

    # Payment entry
    path('payment-entry/select/', views.payment_entry_select, name='payment_entry_select'),
    path('payment-entry/<int:order_id>/', views.payment_entry, name='payment_entry'),

    # Order actions
    path('edit_order/<int:order_id>/', views.edit_order, name='edit_order'),
    path('delete_order/<int:order_id>/', views.delete_order, name='delete_order'),
    path('deliver_order/<int:order_id>/', views.deliver_order, name='deliver_order'),
]
