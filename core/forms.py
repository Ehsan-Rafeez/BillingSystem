from django import forms

from .models import Shop


class ShopInvoiceSettingsForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = [
            "invoice_shop_name",
            "invoice_logo",
            "bank_name",
            "bank_account_title",
            "bank_account_number",
            "bank_iban",
            "bank_branch",
            "bank_branch_code",
            "bank_swift_code",
            "bank_payment_instructions",
            "show_invoice_shop_name",
            "show_invoice_logo",
            "show_invoice_bank_details",
        ]
        widgets = {
            "invoice_shop_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Name shown on invoice"}),
            "invoice_logo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "bank_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Meezan Bank"}),
            "bank_account_title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Account title"}),
            "bank_account_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Account number"}),
            "bank_iban": forms.TextInput(attrs={"class": "form-control", "placeholder": "PK00 BANK 0000 0000 0000 0000"}),
            "bank_branch": forms.TextInput(attrs={"class": "form-control", "placeholder": "Branch name / city"}),
            "bank_branch_code": forms.TextInput(attrs={"class": "form-control", "placeholder": "Branch code"}),
            "bank_swift_code": forms.TextInput(attrs={"class": "form-control", "placeholder": "SWIFT / BIC code"}),
            "bank_payment_instructions": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Any extra payment notes, JazzCash/EasyPaisa detail, advance policy, etc.",
                }
            ),
            "show_invoice_shop_name": forms.CheckboxInput(attrs={"class": "form-check-input", "role": "switch"}),
            "show_invoice_logo": forms.CheckboxInput(attrs={"class": "form-check-input", "role": "switch"}),
            "show_invoice_bank_details": forms.CheckboxInput(attrs={"class": "form-check-input", "role": "switch"}),
        }
