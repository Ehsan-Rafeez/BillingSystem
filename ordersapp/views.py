# ordersapp/views.py

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime

from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods

from .models import Order, Payment


# -----------------------
# Helpers
# -----------------------
def safe_decimal(val, default="0.00"):
    """
    Parse strings to Decimal safely. Trims spaces and empty strings.
    Rounds to 2dp for money using bankers rounding by default.
    """
    try:
        d = Decimal((val or "").strip() or default)
    except (InvalidOperation, AttributeError):
        d = Decimal(default)
    # normalize to 2 decimal places
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def clamp_received(total: Decimal, received: Decimal) -> Decimal:
    """Ensure 0 <= received <= total (if total >= 0)."""
    if received < 0:
        return Decimal("0.00")
    if total >= 0 and received > total:
        return total
    return received


def clean_phone(val: str) -> str:
    """
    Keep digits only; if starts with '0' or '92', normalize lightly.
    Doesn't enforce strict formats—just removes junk.
    """
    digits = "".join(ch for ch in (val or "") if ch.isdigit())
    return digits[:15]  # hard cap to avoid garbage


def safe_date(val):
    """Return YYYY-MM-DD string or None (lets model handle date conversion)."""
    if not val:
        return None
    try:
        # Accept 'YYYY-MM-DD' or similar browser date inputs
        dt = datetime.strptime(val, "%Y-%m-%d").date()
        return dt.isoformat()
    except Exception:
        return None


# -----------------------
# Create Order View
# -----------------------
@require_http_methods(["GET", "POST"])
def create_order(request):
    if request.method == "POST":
        order_name = (request.POST.get("order_name") or "").strip()
        customer_name = (request.POST.get("customer_name") or "").strip()
        address = (request.POST.get("address") or "").strip()
        phone_number = clean_phone(request.POST.get("phone_number"))
        location = (request.POST.get("location") or "").strip()
        delivery_date = safe_date(request.POST.get("delivery_date"))

        total_amount = safe_decimal(request.POST.get("total_amount"), "0.00")
        received_now = safe_decimal(request.POST.get("received_amount"), "0.00")

        # Basic validation
        if total_amount < 0:
            messages.error(request, "Total amount cannot be negative.")
            return render(request, "ordersapp/create_orders.html", {"is_edit": False})

        received_now = clamp_received(total_amount, received_now)

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    order_name=order_name,
                    customer_name=customer_name,
                    address=address,
                    phone_number=phone_number,
                    location=location,
                    delivery_date=delivery_date,
                    total_amount=total_amount,
                    received_amount=received_now,
                )

                # If any cash received at creation time, log a Payment row too
                if received_now > 0:
                    Payment.objects.create(order=order, amount=received_now)

            messages.success(request, "🎉 Order created successfully.")
            return redirect("list_orders")

        except Exception as e:
            messages.error(request, f"Could not create order: {e}")
            return render(request, "ordersapp/create_orders.html", {"is_edit": False})

    # GET
    return render(request, "ordersapp/create_orders.html", {"is_edit": False})


# -----------------------
# List Orders View
# -----------------------
@require_http_methods(["GET"])
def list_orders(request):
    orders = Order.objects.all().order_by("-id")
    return render(request, "ordersapp/list_orders.html", {"orders": orders})


# -----------------------
# Payment Entry View
# -----------------------
@require_http_methods(["GET", "POST"])
def payment_entry(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        amount = safe_decimal(request.POST.get("amount"), "0.00")

        if amount <= 0:
            messages.error(request, "Payment amount must be greater than zero.")
            return redirect("payment_entry", order_id=order.id)

        try:
            with transaction.atomic():
                Payment.objects.create(order=order, amount=amount)
                Order.objects.filter(id=order.id).update(
                    received_amount=F("received_amount") + amount
                )
            messages.success(request, "✅ Payment recorded.")
            return redirect("list_orders")
        except Exception as e:
            messages.error(request, f"Failed to record payment: {e}")
            return redirect("payment_entry", order_id=order.id)

    # GET
    return render(request, "ordersapp/payment_entry.html", {"order": order})


@require_http_methods(["GET"])
def payment_entry_select(request):
    orders = Order.objects.all().order_by("-id")
    return render(request, "ordersapp/payment_entry_select.html", {"orders": orders})


# -----------------------
# Edit Order View (reuses create_orders.html)
# -----------------------
@require_http_methods(["GET", "POST"])
def edit_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        order.order_name = (request.POST.get("order_name") or "").strip()
        order.customer_name = (request.POST.get("customer_name") or "").strip()
        order.address = (request.POST.get("address") or "").strip()
        order.phone_number = clean_phone(request.POST.get("phone_number"))
        order.location = (request.POST.get("location") or "").strip()
        order.delivery_date = safe_date(request.POST.get("delivery_date"))

        new_total = safe_decimal(request.POST.get("total_amount"), str(order.total_amount or "0.00"))
        new_received = safe_decimal(request.POST.get("received_amount"), str(order.received_amount or "0.00"))

        if new_total < 0:
            messages.error(request, "Total amount cannot be negative.")
            return render(request, "ordersapp/create_orders.html", {"order": order, "is_edit": True})

        # Normalize received vs total
        new_received = clamp_received(new_total, new_received)

        order.total_amount = new_total
        order.received_amount = new_received

        try:
            order.save()
            messages.success(request, "✅ Order updated successfully.")
            return redirect("list_orders")
        except Exception as e:
            messages.error(request, f"Could not update order: {e}")

    # GET
    return render(
        request,
        "ordersapp/create_orders.html",
        {"order": order, "is_edit": True},
    )


# -----------------------
# Delete Order View
# -----------------------
@require_http_methods(["GET", "POST"])
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        try:
            order.delete()
            messages.success(request, "🗑️ Order deleted.")
            return redirect("list_orders")
        except Exception as e:
            messages.error(request, f"Could not delete order: {e}")
            return redirect("list_orders")

    # GET (confirm page)
    return render(request, "ordersapp/delete_order.html", {"order": order})
