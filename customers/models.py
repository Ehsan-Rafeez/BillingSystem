from django.db import models
from core.models import TimeStampedModel

class Customer(TimeStampedModel):
    BUSINESS, INDIVIDUAL = "BUS", "IND"
    TYPES = [(BUSINESS, "Business"), (INDIVIDUAL, "Individual")]
    
    # Customer Fields
    customer_id = models.CharField(max_length=100, unique=True, blank=True, null=True)  # Auto-generated ID
    name = models.CharField(max_length=255)
    customer_type = models.CharField(max_length=3, choices=TYPES, default=BUSINESS)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    cnic = models.CharField(max_length=50, blank=True)  # CNIC/ID
    tax_number = models.CharField(max_length=50, blank=True)  # GST/NTN
    notes = models.TextField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.customer_id:
            if not self.pk:  # Only generate customer_id after the object is saved and has a valid pk
                super().save(*args, **kwargs)  # Save the instance first to generate pk
            self.customer_id = f"CUST-{self.pk:04d}"  # Format the ID (CUST-0001, CUST-0002, etc.)
        super().save(*args, **kwargs)  # Save again to update the customer_id
