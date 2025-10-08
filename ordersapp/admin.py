from django.contrib import admin
from .models import Order, Payment, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "order_date", "delivery_date", "status", "total_amount", "received_amount")
    list_filter = ("status", "order_date", "delivery_date")
    search_fields = ("customer_name", "phone_number", "address")
    inlines = [OrderItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "amount", "payment_date", "payment_method")
    list_filter = ("payment_method", "payment_date")
    search_fields = ("order__customer_name",)
