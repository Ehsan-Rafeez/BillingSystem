from decimal import Decimal
from django.db import models


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Expense Category"
        verbose_name_plural = "Expense Categories"

    def __str__(self):
        return self.name


class Expense(models.Model):
    CASH = "cash"
    BANK = "bank"
    CARD = "card"
    METHODS = [
        (CASH, "Cash"),
        (BANK, "Bank Transfer"),
        (CARD, "Card"),
    ]

    date = models.DateField()
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="expenses")
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    supplier_name = models.CharField(max_length=255, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=10, choices=METHODS, default=CASH)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        cat = self.category.name if self.category else "Uncategorized"
        return f"{cat} - {self.amount}"
