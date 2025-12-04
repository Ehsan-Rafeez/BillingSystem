from django import forms
from .models import Customer as CustomerModel

class CustomerForm(forms.ModelForm):
    class Meta:
        model = CustomerModel
        fields = ["name", "customer_type", "phone", "email", "address", "cnic", "tax_number", "notes"]

    def clean_name(self):
        print('clean_name called')
        name = self.cleaned_data.get("name", "").strip()
        if not name:
            raise forms.ValidationError("Name is required.")
        return name
    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")
        return phone

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