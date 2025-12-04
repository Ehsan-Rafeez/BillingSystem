from django.db import models
from decimal import Decimal
from core.models import TimeStampedModel


# -----------------------------
# Base Inventory Model
# -----------------------------
class InventoryBaseItem(TimeStampedModel):
    """
    Base model for tracking inventory items (ingredients, consumables, assets, services).
    Ye system-level inventory ke liye hai (not payment/stock).
    """

    RAW = "RAW"
    CONSUMABLE = "CONS"
    ASSET = "ASSET"
    SERVICE = "SVC"

    TYPES = [
        (RAW, "Raw"),
        (CONSUMABLE, "Consumable"),
        (ASSET, "Asset"),
        (SERVICE, "Service"),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=0)
    item_type = models.CharField(max_length=20, choices=TYPES, default=RAW)
    uom = models.ForeignKey("UnitOfMeasure", on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_per_uom = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal("0.0000"))

    supplier = models.ForeignKey(
        "suppliers.Supplier",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_items",
    )

    # stock buckets
    qty_on_hand = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0.0000"))
    qty_available = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0.0000"))
    qty_reserved = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0.0000"))
    qty_in_use = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0.0000"))
    qty_damaged = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0.0000"))

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Inventory Base Items"


# -----------------------------
# Unit of Measure Model
# -----------------------------
class UnitOfMeasure(models.Model):
    """Table for Units of Measure (kg, g, L, pcs, etc.)."""

    name = models.CharField(max_length=50, unique=True)
    abbreviation = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"

    class Meta:
        verbose_name_plural = "Units of Measure"


# -----------------------------
# Inventory Category Model (NEW)
# -----------------------------
class InventoryCategory(models.Model):
    """Dynamic categories for inventory items (Fruits, Dairy, Meat, etc.)"""

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Inventory Categories"

    def __str__(self):
        return self.name


# -----------------------------
# Inventory Stock Model
# -----------------------------
class InventoryItem(models.Model):
    """Main model for inventory stock, suppliers, payments, and rentals."""

    PAYMENT_METHODS = [
        ("cash", "Cash"),
        ("bank", "Bank Transfer"),
        ("credit", "Credit"),
    ]

    RENT_TYPES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    # Stock Info
    stock_code = models.CharField(max_length=20, unique=True, editable=False)
    name = models.CharField(max_length=255)

    # ✅ ForeignKey to dynamic category instead of static choices
    category = models.ForeignKey(InventoryCategory, on_delete=models.PROTECT, related_name="items")

    quantity = models.PositiveIntegerField(default=1)
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=2)
    uom = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    description = models.TextField(blank=True, null=True)

    # Supplier Info
    supplier_name = models.CharField(max_length=255)
    supplier_phone = models.CharField(max_length=20, blank=True, null=True)
    supplier_cnic = models.CharField(max_length=20, blank=True, null=True)
    supplier_address = models.TextField(blank=True, null=True)

    # Payment Info
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default="cash")
    min_quantity = models.PositiveIntegerField(default=0, help_text="Warn when quantity is at or below this level")

    # Rent Info (optional)
    rent_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    rent_type = models.CharField(max_length=20, choices=RENT_TYPES, blank=True, null=True)
    rent_condition = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Auto-generate stock code if not exists."""
        if not self.stock_code:
            last_id = InventoryItem.objects.count() + 1
            self.stock_code = f"STK-{last_id:04d}"
        super().save(*args, **kwargs)

    @property
    def remaining(self):
        """Return remaining amount = total - paid"""
        return (self.total_amount or 0) - (self.paid_amount or 0)

    def __str__(self):
        return f"{self.stock_code} - {self.name}"

    class Meta:
        verbose_name_plural = "Inventory Items"


class StockMovement(models.Model):
    IN = "IN"
    OUT = "OUT"
    ADJUST = "ADJ"
    TYPES = [
        (IN, "In"),
        (OUT, "Out"),
        (ADJUST, "Adjust"),
    ]

    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name="movements")
    movement_type = models.CharField(max_length=4, choices=TYPES)
    quantity = models.DecimalField(max_digits=14, decimal_places=4)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.inventory_item} {self.movement_type} {self.quantity}"
