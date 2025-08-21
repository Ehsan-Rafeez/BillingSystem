from django.db import models
from core.models import TimeStampedModel

class Customer(TimeStampedModel):
    BUSINESS, INDIVIDUAL = "BUS", "IND"
    TYPES = [(BUSINESS, "Business"), (INDIVIDUAL, "Individual")]

    name = models.CharField(max_length=255)
    customer_type = models.CharField(max_length=3, choices=TYPES, default=BUSINESS)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    tax_number = models.CharField(max_length=50, blank=True)  # GST/NTN (optional)
    notes = models.TextField(blank=True)
    address = models.TextField(blank=True)
    

    def __str__(self): return self.name