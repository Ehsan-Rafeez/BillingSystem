from django.contrib import admin

# Register your models here.

from .models import InventoryItem, UnitOfMeasure, InventoryCategory, InventoryBaseItem, StockMovement

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("stock_code", "name", "quantity", "min_quantity", "payment_method", "supplier_name")
    list_filter = ("payment_method", "category", "uom")
    search_fields = ("name", "stock_code", "supplier_name")


admin.site.register(UnitOfMeasure)
admin.site.register(InventoryCategory)
admin.site.register(InventoryBaseItem)
admin.site.register(StockMovement)
