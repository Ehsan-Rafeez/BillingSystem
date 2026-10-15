from django.contrib import admin
from django import forms
from django.contrib.auth.models import User

from .models import ApiToken, Shop


class ShopAdminForm(forms.ModelForm):
    owner_username = forms.CharField(
        label="New owner username",
        required=False,
        help_text="Create a normal shop-owner login. Leave blank if selecting an existing owner above.",
    )
    owner_password = forms.CharField(
        label="New owner password",
        required=False,
        widget=forms.PasswordInput(
            render_value=False,
            attrs={"class": "shop-owner-password"},
        ),
    )
    owner_password_confirm = forms.CharField(
        label="Confirm owner password",
        required=False,
        widget=forms.PasswordInput(
            render_value=False,
            attrs={"class": "shop-owner-password"},
        ),
        help_text="Enter the same password again.",
    )
    owner_email = forms.EmailField(label="New owner email", required=False)

    class Meta:
        model = Shop
        fields = "__all__"

    class Media:
        js = ("core/admin_password.js",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "owner" in self.fields:
            self.fields["owner"].required = bool(self.instance.pk)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("owner_username")
        password = cleaned_data.get("owner_password")
        password_confirm = cleaned_data.get("owner_password_confirm")

        if self.instance.pk and username:
            raise forms.ValidationError("Edit the existing owner account from Users, or choose another owner.")
        if not self.instance.pk and not username:
            self.add_error("owner_username", "Enter a username for the shop owner.")
        if username and not password:
            self.add_error("owner_password", "Enter a password for the new shop owner.")
        if username and password and password != password_confirm:
            self.add_error("owner_password_confirm", "The passwords do not match.")
        if username and User.objects.filter(username=username).exists():
            self.add_error("owner_username", "A user with this username already exists.")

        return cleaned_data


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    form = ShopAdminForm
    list_display = (
        "name",
        "owner",
        "phone",
        "subscription_plan",
        "subscription_status",
        "subscription_expires_on",
        "is_active",
    )
    list_filter = ("subscription_plan", "subscription_status", "is_active")
    search_fields = ("name", "owner__username", "owner__email", "phone")
    prepopulated_fields = {"slug": ("name",)}

    def get_exclude(self, request, obj=None):
        if obj:
            return ("owner_username", "owner_password", "owner_password_confirm", "owner_email")
        return ("owner",)

    def get_fieldsets(self, request, obj=None):
        owner_fields = ("owner",) if obj else (
            "owner_username",
            "owner_password",
            "owner_password_confirm",
            "owner_email",
        )
        owner_description = (
            "This shop owner is a normal app user, not staff and not super-admin."
            if obj
            else "Create the normal shop-owner login for this shop. This account is not staff and not super-admin."
        )
        return (
            ("Client shop", {"fields": ("name", "slug", "phone", "address", "is_active")}),
            (
                "Shop owner login",
                {
                    "fields": owner_fields,
                    "description": owner_description,
                },
            ),
            (
                "Subscription",
                {
                    "fields": (
                        "subscription_plan",
                        "subscription_status",
                        "subscription_starts_on",
                        "subscription_expires_on",
                        "subscription_notes",
                    )
                },
            ),
        )

    def save_model(self, request, obj, form, change):
        username = form.cleaned_data.get("owner_username")
        if username:
            owner = User(
                username=username,
                email=form.cleaned_data.get("owner_email") or "",
                is_staff=False,
                is_superuser=False,
                is_active=True,
            )
            owner.set_password(form.cleaned_data["owner_password"])
            owner.save()
            obj.owner = owner
        super().save_model(request, obj, form, change)


@admin.register(ApiToken)
class ApiTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "last_used_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("token", "created_at", "last_used_at")
