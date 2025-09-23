# ordersapp/models.py
from django.db import models
from django.utils import timezone


class Order(models.Model):
    order_name = models.CharField(max_length=255)
    customer_name = models.CharField(max_length=255)
    address = models.TextField()
    phone_number = models.CharField(max_length=20)
    location = models.CharField(max_length=255, blank=True, null=True)
    delivery_date = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    received_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # default added

    def __str__(self):
        return f"{self.order_name} - {self.customer_name}"

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
    payment_date = models.DateField(default=timezone.now)   # added field
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS, default="Cash")  # added field
    created_at = models.DateTimeField(auto_now_add=True)  # timestamp

    def __str__(self):
        return f"Payment of {self.amount} for {self.order.order_name}"
