from django import forms
from .models import Customer as CustomerModel


def normalize_pk_mobile(phone):
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    if digits.startswith("0092"):
        digits = digits[4:]
    elif digits.startswith("92"):
        digits = digits[2:]
    if digits.startswith("0"):
        digits = digits[1:]
    if len(digits) != 10 or not digits.startswith("3"):
        raise forms.ValidationError("Enter a valid Pakistani mobile number, e.g. 3028934060 after +92.")
    return f"92{digits}"

class CustomerForm(forms.ModelForm):
    class Meta:
        model = CustomerModel
        fields = ["name", "customer_type", "phone", "email", "address", "cnic", "tax_number", "notes"]

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()
        if not name:
            raise forms.ValidationError("Name is required.")
        return name
    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if not phone:
            return phone
        return normalize_pk_mobile(phone)

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if "@example.com" in email:  # example rule
            raise forms.ValidationError("Emails from example.com are not allowed.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        # cross-field validation
        if cleaned_data.get("customer_type") == "company" and not cleaned_data.get("address"):
            raise forms.ValidationError("Company customers must provide an address.")
        return cleaned_data
