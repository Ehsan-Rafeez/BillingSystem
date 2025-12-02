from django import forms
from django.forms import inlineformset_factory
from .models import Event, MenuItem, MenuCategory, MenuPackage, Quote, QuoteItem


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "customer",
            "title",
            "event_type",
            "event_date",
            "event_time",
            "location",
            "guest_count",
            "dietary_notes",
            "billing_contact_name",
            "billing_contact_phone",
            "billing_contact_email",
            "additional_notes",
        ]
        widgets = {
            "event_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "event_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "dietary_notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "additional_notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "location": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in self.Meta.widgets:
                continue
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " form-control").strip()

    def clean_guest_count(self):
        guest_count = self.cleaned_data.get("guest_count") or 0
        if guest_count < 0:
            raise forms.ValidationError("Guest count cannot be negative.")
        return guest_count


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ["category", "name", "description", "price_per_portion", "is_buffet", "is_addon", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in self.Meta.widgets:
                continue
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " form-control").strip()


class MenuCategoryForm(forms.ModelForm):
    class Meta:
        model = MenuCategory
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        existing = self.fields["name"].widget.attrs.get("class", "")
        self.fields["name"].widget.attrs["class"] = (existing + " form-control").strip()


class MenuPackageForm(forms.ModelForm):
    class Meta:
        model = MenuPackage
        fields = ["name", "description", "price_per_head", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in self.Meta.widgets:
                continue
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " form-control").strip()


class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ["event", "title", "status", "valid_until", "discount_pct", "notes"]
        widgets = {
            "valid_until": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in self.Meta.widgets:
                continue
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " form-control").strip()


class QuoteItemForm(forms.ModelForm):
    class Meta:
        model = QuoteItem
        fields = ["menu_item", "description", "quantity", "unit_price"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " form-control").strip()


QuoteItemFormSet = inlineformset_factory(
    Quote,
    QuoteItem,
    form=QuoteItemForm,
    extra=1,
    can_delete=True,
)
