from django import forms
from .models import InventoryBaseItem, UnitOfMeasure, InventoryCategory


class InventoryBaseItemForm(forms.ModelForm):
    class Meta:
        model = InventoryBaseItem
        fields = [
            "name",
            "description",
            "quantity",
            "item_type",
            "uom",
            "price",
            "cost_per_uom",
            "supplier",
            "qty_on_hand",
            "qty_available",
            "qty_reserved",
            "qty_in_use",
            "qty_damaged",
            "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in self.Meta.widgets:
                continue
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " form-control").strip()


class UnitOfMeasureForm(forms.ModelForm):
    class Meta:
        model = UnitOfMeasure
        fields = ["name", "abbreviation"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " form-control").strip()


class InventoryCategoryForm(forms.ModelForm):
    class Meta:
        model = InventoryCategory
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        css = self.fields["name"].widget.attrs.get("class", "")
        self.fields["name"].widget.attrs["class"] = (css + " form-control").strip()
