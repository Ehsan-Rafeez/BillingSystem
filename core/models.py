from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from pathlib import Path
import secrets


class Shop(models.Model):
    PLAN_BASIC = "basic"
    PLAN_STANDARD = "standard"
    PLAN_PREMIUM = "premium"

    PLAN_CHOICES = (
        (PLAN_BASIC, "Basic"),
        (PLAN_STANDARD, "Standard"),
        (PLAN_PREMIUM, "Premium"),
    )

    SUBSCRIPTION_TRIAL = "trial"
    SUBSCRIPTION_ACTIVE = "active"
    SUBSCRIPTION_PAST_DUE = "past_due"
    SUBSCRIPTION_SUSPENDED = "suspended"
    SUBSCRIPTION_CANCELLED = "cancelled"

    SUBSCRIPTION_STATUS_CHOICES = (
        (SUBSCRIPTION_TRIAL, "Trial"),
        (SUBSCRIPTION_ACTIVE, "Active"),
        (SUBSCRIPTION_PAST_DUE, "Past due"),
        (SUBSCRIPTION_SUSPENDED, "Suspended"),
        (SUBSCRIPTION_CANCELLED, "Cancelled"),
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name="owned_shops")
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    invoice_shop_name = models.CharField(max_length=255, blank=True)
    invoice_logo = models.FileField(upload_to="shop_logos/", blank=True)
    invoice_bank_details = models.TextField(blank=True)
    bank_name = models.CharField(max_length=255, blank=True)
    bank_account_title = models.CharField(max_length=255, blank=True)
    bank_account_number = models.CharField(max_length=100, blank=True)
    bank_iban = models.CharField(max_length=100, blank=True)
    bank_branch = models.CharField(max_length=255, blank=True)
    bank_branch_code = models.CharField(max_length=50, blank=True)
    bank_swift_code = models.CharField(max_length=50, blank=True)
    bank_payment_instructions = models.TextField(blank=True)
    show_invoice_shop_name = models.BooleanField(default=True)
    show_invoice_logo = models.BooleanField(default=True)
    show_invoice_bank_details = models.BooleanField(default=True)
    subscription_plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_BASIC)
    subscription_status = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_STATUS_CHOICES,
        default=SUBSCRIPTION_TRIAL,
    )
    subscription_starts_on = models.DateField(blank=True, null=True)
    subscription_expires_on = models.DateField(blank=True, null=True)
    subscription_notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "shop"
            slug = base
            counter = 2
            while Shop.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def displayable_invoice_logo(self):
        """Whether the stored logo can be rendered directly by a browser."""
        if not self.invoice_logo:
            return False
        return Path(self.invoice_logo.name).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}


class ApiToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_tokens")
    token = models.CharField(max_length=64, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"API token for {self.user}"


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True
