from django.db import models
from decimal import Decimal
from core.models import TimeStampedModel


class Supplier(TimeStampedModel):
    """Model representing a supplier for inventory items."""
    
    BUSINESS, INDIVIDUAL = "BUS", "IND"
    TYPES = [(BUSINESS, "Business"), (INDIVIDUAL, "Individual")]
    
    # Supplier Fields
    supplier_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    name = models.CharField(max_length=255)
    supplier_type = models.CharField(max_length=3, choices=TYPES, default=BUSINESS)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    contact_person = models.CharField(max_length=255, blank=True)
    tax_number = models.CharField(max_length=50, blank=True)  # GST/NTN
    notes = models.TextField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Payment tracking fields
    total_purchases = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    
    def __str__(self):
        return self.name
    
    @property
    def balance_due(self):
        """Calculate remaining balance due to supplier"""
        return self.total_purchases - self.total_paid
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.supplier_id:
            self.supplier_id = f"SUP-{self.pk:04d}"
            super().save(update_fields=['supplier_id'])
    
    class Meta:
        verbose_name_plural = "Suppliers"


class SupplierPayment(TimeStampedModel):
    """Model for tracking payments made to suppliers."""
    
    PAYMENT_METHODS = [
        ("Cash", "Cash"),
        ("Bank", "Bank Transfer"),
        ("Card", "Credit/Debit Card"),
        ("Check", "Check"),
        ("Other", "Other"),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS, default="Cash")
    reference_number = models.CharField(max_length=100, blank=True)  # Check number, transaction ID, etc.
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Payment of {self.amount} to {self.supplier.name} on {self.payment_date}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update supplier's total_paid when a payment is saved
        self.supplier.total_paid = sum(
            payment.amount for payment in self.supplier.payments.all()
        )
        self.supplier.save(update_fields=['total_paid'])
    
    def delete(self, *args, **kwargs):
        supplier = self.supplier
        super().delete(*args, **kwargs)
        # Update supplier's total_paid when a payment is deleted
        supplier.total_paid = sum(
            payment.amount for payment in supplier.payments.all()
        )
        supplier.save(update_fields=['total_paid'])
    
    class Meta:
        verbose_name_plural = "Supplier Payments"
        ordering = ['-payment_date']


class PurchaseOrder(TimeStampedModel):
    """Model for tracking purchase orders from suppliers."""
    
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (PARTIAL, "Partially Received"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    order_number = models.CharField(max_length=100, unique=True)
    order_date = models.DateField()
    expected_delivery_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"PO-{self.order_number} - {self.supplier.name}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.order_number:
            self.order_number = f"PO-{self.pk:06d}"
            super().save(update_fields=['order_number'])
    
    class Meta:
        verbose_name_plural = "Purchase Orders"
        ordering = ['-order_date']


class PurchaseOrderItem(models.Model):
    """Model for individual items in a purchase order."""
    
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    inventory_item = models.ForeignKey('inventory.InventoryItem', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=14, decimal_places=4)
    unit_price = models.DecimalField(max_digits=12, decimal_places=4)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"{self.inventory_item.name} - {self.quantity} @ {self.unit_price}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        
        # Update purchase order total
        self.purchase_order.total_amount = sum(
            item.total_price for item in self.purchase_order.items.all()
        )
        self.purchase_order.save(update_fields=['total_amount'])
        
        # Update supplier's total_purchases
        self.purchase_order.supplier.total_purchases = sum(
            po.total_amount for po in self.purchase_order.supplier.purchase_orders.all()
        )
        self.purchase_order.supplier.save(update_fields=['total_purchases'])
    
    class Meta:
        verbose_name_plural = "Purchase Order Items"