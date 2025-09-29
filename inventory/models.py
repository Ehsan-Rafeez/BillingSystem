from decimal import Decimal
from django.db import models
from core.models import TimeStampedModel


class InventoryItem(TimeStampedModel):
    """Model representing an item in the inventory (Buy, Rent, Order)."""

    # Categories
    RAW = "RAW"           # Buy
    ASSET = "ASSET"       # Rent
    ORDER = "ORDER"       # Order
    TYPES = [
        (RAW, "Buy"),
        (ASSET, "Rent"),
        (ORDER, "Order"),
    ]

    # Auto stock code (e.g., STK-0001)
    stock_code = models.CharField(max_length=20, unique=True, editable=False)

    # Customer Information
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    customer_cnic = models.CharField(max_length=20, blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    customer_address = models.TextField(blank=True, null=True)

    # Item Information
    description = models.TextField(blank=True)
    items_taken = models.TextField(blank=True)  # auto mirror of description
    item_type = models.CharField(max_length=20, choices=TYPES, default=RAW)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # Rent-specific fields
    rent_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    RENT_TYPES = [("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")]
    rent_type = models.CharField(max_length=20, choices=RENT_TYPES, blank=True, null=True)
    rent_condition = models.TextField(blank=True, null=True)
    is_returned = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Save hook
    def save(self, *args, **kwargs):
        # Generate stock code if not exists
        if not self.stock_code:
            last_id = InventoryItem.objects.count() + 1
            self.stock_code = f"STK-{last_id:04d}"

        # Auto copy description to items_taken
        if self.description and not self.items_taken:
            self.items_taken = self.description

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.stock_code}"

    class Meta:
        verbose_name_plural = "Inventory Items"
