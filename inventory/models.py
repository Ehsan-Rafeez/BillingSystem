from django.db import models
from decimal import Decimal


class UnitOfMeasure(models.Model):
    """Table for Units of Measure (kg, g, L, pcs, etc.)."""
    name = models.CharField(max_length=50, unique=True)
    abbreviation = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"

    class Meta:
        verbose_name_plural = "Units of Measure"


class InventoryItem(models.Model):
    """Model representing an item in the inventory."""

    # ✅ Grocery Inventory Categories
    CATEGORY_CHOICES = [
        ("produce", "Fruits & Vegetables"),
        ("dairy", "Dairy & Eggs"),
        ("meat", "Meat & Poultry"),
        ("bakery", "Bakery & Breads"),
        ("pantry", "Pantry Staples"),
        ("beverages", "Beverages"),
        ("snacks", "Snacks & Packaged Foods"),
        ("frozen", "Frozen Foods"),
        ("canned", "Canned & Jarred Goods"),
        ("health", "Health & Personal Care"),
        ("household", "Household Essentials"),
        ("baby", "Baby Products"),
        ("pet", "Pet Food & Supplies"),
    ]

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
    stock_code = models.CharField(max_length=20, unique=True, editable=False)  # Auto generated
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
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

    # Rent Info (optional – if needed for rental items like freezers, trolleys etc.)
    rent_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    rent_type = models.CharField(max_length=20, choices=RENT_TYPES, blank=True, null=True)
    rent_condition = models.TextField(blank=True, null=True)

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Auto-generate stock code if not exists."""
        if not self.stock_code:
            last_id = InventoryItem.objects.count() + 1
            self.stock_code = f"STK-{last_id:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.stock_code} - {self.name}"

    class Meta:
        verbose_name_plural = "Inventory Items"
