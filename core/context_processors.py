from datetime import timedelta

from django.utils.timezone import localdate

from ordersapp.models import Order

from .tenancy import tenant_queryset


def order_reminders(request):
    """Provide shop-scoped upcoming and overdue order reminders to shared templates."""
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {
            "upcoming_order_reminders": [],
            "overdue_order_reminders": [],
            "order_reminder_count": 0,
        }

    today = localdate()
    next_seven_days = today + timedelta(days=7)
    pending_orders = tenant_queryset(
        request,
        Order.objects.filter(status=Order.STATUS_PENDING),
    )
    upcoming = list(
        pending_orders.filter(
            delivery_date__gte=today,
            delivery_date__lte=next_seven_days,
        ).order_by("delivery_date", "delivery_time", "id")[:8]
    )
    overdue = list(
        pending_orders.filter(delivery_date__lt=today)
        .order_by("delivery_date", "id")[:8]
    )

    return {
        "upcoming_order_reminders": upcoming,
        "overdue_order_reminders": overdue,
        "order_reminder_count": len(upcoming) + len(overdue),
    }
