from decimal import Decimal

from django.db import models
from django.utils import timezone
from customers.models import Customer


class Event(models.Model):
    """Event/Booking for catering jobs."""

    WEDDING = "wedding"
    CORPORATE = "corporate"
    PARTY = "party"
    OTHER = "other"
    EVENT_TYPES = [
        (WEDDING, "Wedding"),
        (CORPORATE, "Corporate"),
        (PARTY, "Private Party"),
        (OTHER, "Other"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="events")
    title = models.CharField(max_length=255, help_text="Event name or identifier")
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default=OTHER)
    event_date = models.DateField()
    event_time = models.TimeField(blank=True, null=True)
    location = models.TextField()
    guest_count = models.PositiveIntegerField(default=0)
    dietary_notes = models.TextField(blank=True)
    billing_contact_name = models.CharField(max_length=255, blank=True)
    billing_contact_phone = models.CharField(max_length=50, blank=True)
    billing_contact_email = models.EmailField(blank=True)
    additional_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.event_date})"

    class Meta:
        ordering = ["-event_date", "-id"]
        verbose_name = "Event"
        verbose_name_plural = "Events"


class MenuCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category = models.ForeignKey(MenuCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="items")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price_per_portion = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    is_buffet = models.BooleanField(default=False)
    is_addon = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class RecipeItem(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="recipe_items")
    inventory_item = models.ForeignKey("inventory.InventoryItem", on_delete=models.PROTECT)
    quantity_per_portion = models.DecimalField(max_digits=12, decimal_places=4)

    def __str__(self):
        return f"{self.menu_item} -> {self.inventory_item}"


class MenuPackage(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price_per_head = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    items = models.ManyToManyField(MenuItem, through="MenuPackageItem", related_name="packages")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class MenuPackageItem(models.Model):
    package = models.ForeignKey(MenuPackage, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    portions = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("package", "menu_item")


class Order(models.Model):
    ORDER_TYPES = [
        ('regular', 'Regular'),
        ('premium', 'Premium'),
        ('vip', 'VIP'),
    ]

    STATUS_PENDING = "PENDING"
    STATUS_DELIVERED = "DELIVERED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_DELIVERED, "Delivered"),
    ]


    order_date = models.DateField()
    customer_name = models.CharField(max_length=255)
    address = models.TextField()
    phone_number = models.CharField(max_length=20)
    
    location = models.CharField(max_length=255, blank=True, null=True)
    delivery_date = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    received_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cnic_number = models.CharField(max_length=20, blank=False, null=False, default="0000000000000")
    
    # Added fields
    customer_type = models.CharField(max_length=20, choices=ORDER_TYPES, default='regular')
    email = models.EmailField(max_length=255, blank=True, default='')

    # Delivery/fulfilment
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    delivered_at = models.DateTimeField(blank=True, null=True)

    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")

    def __str__(self):
        return f"{self.customer_name} - {self.order_date}"

    @property
    def due_amount(self):
        """Calculate remaining due amount"""
        return self.total_amount - self.received_amount


class Payment(models.Model):
    PAYMENT_METHODS = [
        ("Cash", "Cash"),
        ("Bank", "Bank Transfer"),
        ("Card", "Credit/Debit Card"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)  # added field
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS, default="Cash")  # added field
    created_at = models.DateTimeField(auto_now_add=True)  # timestamp

    def __str__(self):
        return f"Payment of {self.amount} for {self.order.customer_name}"


class Quote(models.Model):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    STATUS_CHOICES = [
        (DRAFT, "Draft"),
        (SENT, "Sent"),
        (ACCEPTED, "Accepted"),
        (REJECTED, "Rejected"),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="quotes")
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    valid_until = models.DateField(blank=True, null=True)
    discount_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def recalc_totals(self):
        subtotal = sum((item.line_total or Decimal("0.00")) for item in self.items.all())
        discount = (subtotal * (self.discount_pct or Decimal("0.00")) / Decimal("100")).quantize(Decimal("0.01"))
        self.total_amount = subtotal - discount
        return self.total_amount


class QuoteItem(models.Model):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField(default=1, help_text="Portions or units")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    def save(self, *args, **kwargs):
        if self.menu_item and not self.description:
            self.description = self.menu_item.name
        self.line_total = (self.unit_price or Decimal("0.00")) * self.quantity
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='items')
    inventory_item = models.ForeignKey('inventory.InventoryItem', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.inventory_item.name} x {self.quantity}"


class OrderMenuItem(models.Model):
    """Order line for menu items (dishes/packages)"""

    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='menu_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(help_text="Portions or kg as entered")
    note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.menu_item.name} x {self.quantity}"

