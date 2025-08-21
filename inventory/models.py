from decimal import Decimal
from django.db import models
from core.models import TimeStampedModel

# Create your models here.

class InventoryItem(TimeStampedModel):
    """Model representing an item in the inventory.
    """
    RAW = "RAW"           # ingredients that are consumed
    CONSUMABLE = "CONS"   # disposables (napkins, boxes)
    ASSET = "ASSET"       # reusable/rentable items (chairs, chafing dishes)
    SERVICE = "SVC"       # optional: technician hours etc (no stock tracking)
    TYPES = [(RAW,"Raw"), (CONSUMABLE,"Consumable"), (ASSET,"Asset"), (SERVICE,"Service")]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=0)
    item_type = models.CharField(max_length=20, choices=TYPES, default=RAW)
    uom = models.ForeignKey('UnitOfMeasure', on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_per_uom = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal("0.0000"))

    # stock buckets
    qty_on_hand = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0.0000"))
    qty_available = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0.0000"))  # on_hand - reserved - in_use
    qty_reserved = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0.0000"))   # reserved for future events
    qty_in_use   = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0.0000"))   # currently out (rented/used)
    qty_damaged  = models.DecimalField(max_digits=14, decimal_places=4, default=Decimal("0.0000"))   # damaged/awaiting repair

    # is_serialized = models.BooleanField(default=False)  # set True if you track each unit separately (e.g., “Chair #A001”)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Inventory Items"


class UnitOfMeasure(models.Model):
    name = models.CharField(max_length=50, unique=True)
    abbreviation = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"

    class Meta:
        verbose_name_plural = "Units of Measure"