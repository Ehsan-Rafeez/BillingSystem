from datetime import date, timedelta
from django.db.models import Sum, Count, F, Case, When, DecimalField, Value
from django.db.models.functions import Coalesce
from django.shortcuts import render

from ordersapp.models import Order  # apka model

def index(request):
    today = date.today()
    next_7 = today + timedelta(days=7)

    # Aggregates
    totals = Order.objects.aggregate(
        total_orders=Count("id"),
        total_billed=Coalesce(Sum("total_amount"), Value(0), output_field=DecimalField(max_digits=12, decimal_places=2)),
        total_received=Coalesce(Sum("received_amount"), Value(0), output_field=DecimalField(max_digits=12, decimal_places=2)),
        outstanding=Coalesce(
            Sum(
                Case(
                    When(total_amount__gt=F("received_amount"),
                         then=F("total_amount") - F("received_amount")),
                    default=Value(0),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            ),
            Value(0),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
    )

    # Status counts
    status_counts = Order.objects.aggregate(
        unpaid=Count(Case(When(received_amount__lte=0, then=1))),
        partial=Count(Case(When(received_amount__gt=0, total_amount__gt=F("received_amount"), then=1))),
        paid=Count(Case(When(total_amount__lte=F("received_amount"), then=1))),
    )

    # Deliveries
    todays_deliveries = Order.objects.filter(delivery_date=today).count()
    upcoming_deliveries = Order.objects.filter(delivery_date__gt=today, delivery_date__lte=next_7).count()

    # Customers
    total_customers = Order.objects.values("customer_name").distinct().count()

    # Recent orders
    recent_orders = Order.objects.order_by("-id")[:8]

    context = {
        "total_orders": totals["total_orders"] or 0,
        "total_billed": totals["total_billed"],
        "total_received": totals["total_received"],
        "outstanding": totals["outstanding"],
        "pending_due": totals["outstanding"],
        "pending_orders": status_counts["unpaid"] + status_counts["partial"],
        "unpaid_orders": status_counts["unpaid"],
        "partial_orders": status_counts["partial"],
        "paid_orders": status_counts["paid"],
        "today_deliveries": todays_deliveries,
        "upcoming_deliveries": upcoming_deliveries,
        "total_customers": total_customers,
        "recent_orders": recent_orders,
    }

    return render(request, "core/index.html", context)
