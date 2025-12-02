from django.contrib import admin
from .models import Order, Payment, OrderItem, Event, MenuItem, MenuCategory, RecipeItem, MenuPackage, MenuPackageItem, Quote, QuoteItem, OrderMenuItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ("inventory_item", "quantity", "note")


class OrderMenuItemInline(admin.TabularInline):
    model = OrderMenuItem
    extra = 1
    fields = ("menu_item", "quantity", "note")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "customer", "event_type", "event_date", "guest_count")
    list_filter = ("event_type", "event_date")
    search_fields = ("title", "customer__name", "location")


class RecipeItemInline(admin.TabularInline):
    model = RecipeItem
    extra = 1


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price_per_portion", "is_buffet", "is_addon", "is_active")
    list_filter = ("is_buffet", "is_addon", "is_active", "category")
    search_fields = ("name", "description")
    inlines = [RecipeItemInline]


class MenuPackageItemInline(admin.TabularInline):
    model = MenuPackageItem
    extra = 1


@admin.register(MenuPackage)
class MenuPackageAdmin(admin.ModelAdmin):
    list_display = ("name", "price_per_head", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    inlines = [MenuPackageItemInline]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "event", "order_date", "delivery_date", "status", "total_amount", "received_amount")
    list_filter = ("status", "order_date", "delivery_date", "event")
    search_fields = ("customer_name", "phone_number", "address", "event__title")
    inlines = [OrderItemInline, OrderMenuItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "amount", "payment_date", "payment_method")
    list_filter = ("payment_method", "payment_date")
    search_fields = ("order__customer_name",)


class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 1


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("title", "event", "status", "valid_until", "total_amount")
    list_filter = ("status", "valid_until")
    search_fields = ("title", "event__title", "event__customer__name")
    inlines = [QuoteItemInline]
