from django.db import models
from django.utils import timezone


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


class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='items')
    inventory_item = models.ForeignKey('inventory.InventoryItem', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.inventory_item.name} x {self.quantity}"

