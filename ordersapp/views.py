from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime

from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from .models import Order, Payment, OrderItem
from inventory.models import InventoryItem


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
    stock_items = InventoryItem.objects.all().order_by("name")
    if request.method == "POST":
        order_date = safe_date(request.POST.get("order_date"))  # Use order date instead of order name
        customer_name = (request.POST.get("customer_name") or "").strip()
        address = (request.POST.get("address") or "").strip()
        phone_number = clean_phone(request.POST.get("phone_number"))
        location = (request.POST.get("location") or "").strip()
        delivery_date = safe_date(request.POST.get("delivery_date"))
        cnic_number = (request.POST.get("cnic") or "").strip()
        total_amount = safe_decimal(request.POST.get("total_amount"), "0.00")
        received_now = safe_decimal(request.POST.get("received_amount"), "0.00")

        # Parse item selections
        item_ids = request.POST.getlist("item_ids[]")
        quantities = request.POST.getlist("quantities[]")
        parsed_rows = []
        for i, iid in enumerate(item_ids or []):
            try:
                q = int((quantities[i] if i < len(quantities) else "0") or "0")
            except (ValueError, TypeError):
                q = 0
            if not iid or q <= 0:
                continue
            parsed_rows.append((int(iid), q))

        # Basic validation
        if total_amount < 0:
            messages.error(request, "Total amount cannot be negative.")
            return render(request, "ordersapp/create_orders.html", {"is_edit": False, "stock_items": stock_items})

        # Must have at least one item
        if not parsed_rows:
            messages.error(request, "Please add at least one item with quantity.")
            return render(request, "ordersapp/create_orders.html", {"is_edit": False, "stock_items": stock_items})

        received_now = clamp_received(total_amount, received_now)

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    order_date=order_date,  # Storing the order date
                    customer_name=customer_name,
                    address=address,
                    phone_number=phone_number,
                    location=location,
                    delivery_date=delivery_date,
                    total_amount=total_amount,
                    received_amount=received_now,
                    cnic_number=cnic_number,
                )

                # Validate stock availability and create order items
                # Note: we only deduct on delivery, but we can prevent overbooking here
                inv_map = {obj.id: obj for obj in InventoryItem.objects.filter(id__in=[iid for iid, _ in parsed_rows])}
                for iid, q in parsed_rows:
                    inv = inv_map.get(iid)
                    if not inv:
                        raise ValueError("Invalid inventory item selected.")
                    if q > inv.quantity:
                        raise ValueError(f"Insufficient stock for {inv.name}. Requested {q}, available {inv.quantity}.")

                OrderItem.objects.bulk_create([
                    OrderItem(order=order, inventory_item_id=iid, quantity=q)
                    for iid, q in parsed_rows
                ])

                # If any cash received at creation time, log a Payment row too
                if received_now > 0:
                    Payment.objects.create(order=order, amount=received_now)

            messages.success(request, "🎉 Order created successfully.")
            return redirect("list_orders")

        except Exception as e:
            messages.error(request, f"Could not create order: {e}")
            return render(request, "ordersapp/create_orders.html", {"is_edit": False, "stock_items": stock_items})

    # GET
    return render(request, "ordersapp/create_orders.html", {"is_edit": False, "stock_items": stock_items})


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
        order.order_date = safe_date(request.POST.get("order_date"))  # Editing the order date
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


# -----------------------
# Deliver Order (deduct stock)
# -----------------------
@require_http_methods(["POST"]) 
def deliver_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if order.status == Order.STATUS_DELIVERED:
        messages.info(request, "Order already delivered.")
        return redirect("list_orders")

    items = list(order.items.select_related("inventory_item").all())
    if not items:
        messages.error(request, "No items found for this order. Add items before delivering.")
        return redirect("list_orders")

    try:
        with transaction.atomic():
            # Validate stock availability first
            for oi in items:
                inv: InventoryItem = oi.inventory_item
                if oi.quantity > inv.quantity:
                    raise ValueError(f"Insufficient stock for {inv.name}. Needed {oi.quantity}, available {inv.quantity}.")

            # Deduct stock
            for oi in items:
                InventoryItem.objects.filter(id=oi.inventory_item_id).update(
                    quantity=F("quantity") - oi.quantity
                )

            # Mark order delivered
            order.status = Order.STATUS_DELIVERED
            order.delivered_at = timezone.now()
            order.save(update_fields=["status", "delivered_at"])

        messages.success(request, "✅ Order delivered and stock updated.")
    except Exception as e:
        messages.error(request, f"Could not deliver order: {e}")

    return redirect("list_orders")
