from django.contrib import admin
from .models import Supplier, SupplierPayment, PurchaseOrder, PurchaseOrderItem


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['supplier_id', 'name', 'supplier_type', 'phone', 'email', 'total_purchases', 'total_paid', 'balance_due', 'is_active']
    list_filter = ['supplier_type', 'is_active', 'created_at']
    search_fields = ['name', 'supplier_id', 'email', 'phone', 'contact_person']
    readonly_fields = ['supplier_id', 'total_purchases', 'total_paid', 'balance_due', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('supplier_id', 'name', 'supplier_type', 'contact_person')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Business Information', {
            'fields': ('tax_number', 'notes')
        }),
        ('Financial Information', {
            'fields': ('total_purchases', 'total_paid', 'balance_due'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ['inventory_item', 'quantity', 'unit_price', 'total_price']
    readonly_fields = ['total_price']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'supplier', 'order_date', 'expected_delivery_date', 'status', 'total_amount']
    list_filter = ['status', 'order_date', 'supplier']
    search_fields = ['order_number', 'supplier__name']
    readonly_fields = ['order_number', 'total_amount', 'created_at', 'updated_at']
    inlines = [PurchaseOrderItemInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'supplier', 'order_date', 'expected_delivery_date', 'status')
        }),
        ('Financial Information', {
            'fields': ('total_amount',)
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SupplierPayment)
class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = ['supplier', 'amount', 'payment_date', 'payment_method', 'reference_number']
    list_filter = ['payment_method', 'payment_date', 'supplier']
    search_fields = ['supplier__name', 'reference_number', 'notes']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Payment Information', {
            'fields': ('supplier', 'amount', 'payment_date', 'payment_method', 'reference_number')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ['purchase_order', 'inventory_item', 'quantity', 'unit_price', 'total_price']
    list_filter = ['purchase_order__supplier', 'purchase_order__order_date']
    search_fields = ['inventory_item__name', 'purchase_order__order_number']
    readonly_fields = ['total_price']