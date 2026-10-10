from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Shop


def get_current_shop(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return None
    if request.user.is_superuser:
        shop_id = request.session.get("current_shop_id")
        if shop_id:
            return Shop.objects.filter(id=shop_id, is_active=True).first()
        return None
    return Shop.objects.filter(owner=request.user, is_active=True).order_by("id").first()


def tenant_queryset(request, queryset):
    shop = getattr(request, "shop", None)
    if getattr(request.user, "is_superuser", False):
        return queryset
    if shop is None:
        return queryset.none()
    return queryset.filter(shop=shop)


def tenant_or_global_queryset(request, queryset):
    shop = getattr(request, "shop", None)
    if getattr(request.user, "is_superuser", False):
        return queryset
    if shop is None:
        return queryset.none()
    return queryset.filter(Q(shop=shop) | Q(shop__isnull=True))


def tenant_get_object_or_404(request, queryset, **kwargs):
    return get_object_or_404(tenant_queryset(request, queryset), **kwargs)


def assign_shop(request, obj):
    shop = getattr(request, "shop", None)
    if shop is not None and hasattr(obj, "shop_id") and not obj.shop_id:
        obj.shop = shop
    return obj
