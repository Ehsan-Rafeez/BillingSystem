from django.contrib import admin

# Register your models here.

from .models import InventoryItem, UnitOfMeasure, InventoryCategory

admin.site.register(InventoryItem)
admin.site.register(UnitOfMeasure)
admin.site.register(InventoryCategory)
