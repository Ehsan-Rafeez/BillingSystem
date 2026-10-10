from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime

from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.utils import timezone
from django.utils.dateparse import parse_date

from .models import (
    Order,
    Payment,
    OrderItem,
    OrderMenuItem,
    RecipeItem,
    Event,
    MenuItem,
    MenuPackage,
    Quote,
    MenuCategory,
)
from .forms import EventForm, MenuItemForm, MenuPackageForm, QuoteForm, QuoteItemFormSet, MenuCategoryForm
from inventory.models import InventoryItem, StockMovement, UnitOfMeasure, InventoryCategory
from expenses.models import Expense
from customers.models import Customer
from core.tenancy import assign_shop, tenant_get_object_or_404, tenant_or_global_queryset, tenant_queryset


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


def calculate_discounted_total(gross: Decimal, discount: Decimal) -> tuple[Decimal, Decimal]:
    """Return a non-negative discount and net total."""
    if gross < 0:
        gross = Decimal("0.00")
    if discount < 0:
        discount = Decimal("0.00")
    if discount > gross:
        discount = gross
    return discount, gross - discount


def money(value):
    return (value or Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def clean_phone(val: str) -> str:
    digits = "".join(ch for ch in (val or "") if ch.isdigit())
    if digits.startswith("0092"):
        digits = digits[4:]
    elif digits.startswith("92"):
        digits = digits[2:]
    if digits.startswith("0"):
        digits = digits[1:]
    if len(digits) != 10 or not digits.startswith("3"):
        raise ValueError("Phone number must be a valid Pakistani mobile number, e.g. 3028934060 after +92.")
    return f"92{digits}"


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


def safe_time(val):
    if not val:
        return None
    try:
        return datetime.strptime(val, "%H:%M").time()
    except Exception:
        return None


def save_customer_from_order_data(request, name, phone, email, address, cnic):
    name = (name or "").strip()
    phone = (phone or "").strip()
    email = (email or "").strip()
    address = (address or "").strip()
    cnic = (cnic or "").strip()

    if not name:
        return None

    customer = None
    customers = tenant_queryset(request, Customer.objects.all())
    if cnic:
        customer = customers.filter(cnic=cnic).first()
    if customer is None and phone:
        customer = customers.filter(phone=phone).first()
    if customer is None and email:
        customer = customers.filter(email__iexact=email).first()
    if customer is None:
        customer = Customer(name=name, customer_type=Customer.INDIVIDUAL)

    customer.name = name
    customer.phone = phone
    customer.email = email
    customer.address = address
    customer.cnic = cnic
    assign_shop(request, customer)
    customer.save()
    return customer


def ensure_order_inventory_options():
    if UnitOfMeasure.objects.count() == 0:
        for row in [
            {"name": "Kilogram", "abbreviation": "kg"},
            {"name": "Gram", "abbreviation": "g"},
            {"name": "Liter", "abbreviation": "L"},
            {"name": "Piece", "abbreviation": "pc"},
            {"name": "Box", "abbreviation": "box"},
        ]:
            UnitOfMeasure.objects.get_or_create(abbreviation=row["abbreviation"], defaults={"name": row["name"]})

    if InventoryCategory.objects.count() == 0:
        for name in ["Pantry Staples", "Meat & Poultry", "Beverages", "Household Essentials"]:
            InventoryCategory.objects.get_or_create(name=name)


def order_form_context(request, **extra):
    context = {
        "menu_items": tenant_queryset(request, MenuItem.objects.filter(is_active=True)).order_by("name"),
        "menu_categories": tenant_queryset(request, MenuCategory.objects.all()).order_by("name"),
        "pricing_units": MenuItem.PRICING_UNIT_CHOICES,
        "events": tenant_queryset(request, Event.objects.select_related("customer")).order_by("-event_date"),
        "today": timezone.localdate(),
    }
    context.update(extra)
    return context


# -----------------------
# Events / Bookings
# -----------------------
@require_http_methods(["GET"])
def event_list(request):
    events = tenant_queryset(request, Event.objects.select_related("customer")).order_by("-event_date", "-id")
    return render(request, "ordersapp/event_list.html", {"events": events})


@require_http_methods(["GET", "POST"])
def event_create(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            assign_shop(request, event)
            event.save()
            messages.success(request, f"Event '{event.title}' created.")
            return redirect("list_events")
        messages.error(request, "Please fix the errors below.")
    else:
        form = EventForm()
    return render(request, "ordersapp/event_form.html", {"form": form, "is_edit": False})


@require_http_methods(["GET", "POST"])
def event_update(request, event_id):
    event = tenant_get_object_or_404(request, Event.objects.all(), id=event_id)
    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            event = form.save(commit=False)
            assign_shop(request, event)
            event.save()
            messages.success(request, f"Event '{event.title}' updated.")
            return redirect("list_events")
        messages.error(request, "Please fix the errors below.")
    else:
        form = EventForm(instance=event)
    return render(request, "ordersapp/event_form.html", {"form": form, "is_edit": True, "event": event})


# -----------------------
# Menu Items
# -----------------------
@require_http_methods(["GET"])
def menu_list(request):
    items = tenant_queryset(request, MenuItem.objects.select_related("category")).order_by("name")
    categories = tenant_queryset(request, MenuCategory.objects.all()).order_by("name")
    return render(request, "ordersapp/menu_list.html", {"items": items, "categories": categories})


@require_http_methods(["GET", "POST"])
def menu_create(request):
    if request.method == "POST":
        form = MenuItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            assign_shop(request, item)
            item.save()
            messages.success(request, "Menu item created.")
            return redirect("menu_list")
        messages.error(request, "Please fix the errors below.")
    else:
        form = MenuItemForm()
    return render(request, "ordersapp/menu_form.html", {"form": form, "is_edit": False})


@require_http_methods(["GET", "POST"])
def menu_update(request, item_id):
    item = tenant_get_object_or_404(request, MenuItem.objects.all(), id=item_id)
    if request.method == "POST":
        form = MenuItemForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save(commit=False)
            assign_shop(request, item)
            item.save()
            messages.success(request, "Menu item updated.")
            return redirect("menu_list")
        messages.error(request, "Please fix the errors below.")
    else:
        form = MenuItemForm(instance=item)
    return render(request, "ordersapp/menu_form.html", {"form": form, "is_edit": True, "item": item})


# -----------------------
# Menu Categories
# -----------------------
@require_http_methods(["GET"])
def category_list(request):
    categories = tenant_queryset(request, MenuCategory.objects.all()).order_by("name")
    return render(request, "ordersapp/category_list.html", {"categories": categories})


@require_http_methods(["GET", "POST"])
def category_create(request):
    if request.method == "POST":
        form = MenuCategoryForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"].strip()
            if tenant_queryset(request, MenuCategory.objects.all()).filter(name__iexact=name).exists():
                form.add_error("name", "This category already exists.")
                messages.error(request, "Please fix the errors below.")
                return render(request, "ordersapp/category_form.html", {"form": form, "is_edit": False})
            category = form.save(commit=False)
            category.name = name
            assign_shop(request, category)
            category.save()
            messages.success(request, "Category created.")
            return redirect("category_list")
        messages.error(request, "Please fix the errors below.")
    else:
        form = MenuCategoryForm()
    return render(request, "ordersapp/category_form.html", {"form": form, "is_edit": False})


@require_http_methods(["GET", "POST"])
def category_update(request, category_id):
    category = tenant_get_object_or_404(request, MenuCategory.objects.all(), id=category_id)
    if request.method == "POST":
        form = MenuCategoryForm(request.POST, instance=category)
        if form.is_valid():
            name = form.cleaned_data["name"].strip()
            duplicate = tenant_queryset(request, MenuCategory.objects.all()).filter(name__iexact=name).exclude(id=category.id)
            if duplicate.exists():
                form.add_error("name", "This category already exists.")
                messages.error(request, "Please fix the errors below.")
                return render(request, "ordersapp/category_form.html", {"form": form, "is_edit": True, "category": category})
            category = form.save(commit=False)
            category.name = name
            assign_shop(request, category)
            category.save()
            messages.success(request, "Category updated.")
            return redirect("category_list")
        messages.error(request, "Please fix the errors below.")
    else:
        form = MenuCategoryForm(instance=category)
    return render(request, "ordersapp/category_form.html", {"form": form, "is_edit": True, "category": category})


# -----------------------
# Quotes / Proposals
# -----------------------
@require_http_methods(["GET"])
def quote_list(request):
    quotes = tenant_queryset(request, Quote.objects.select_related("event", "event__customer")).order_by("-id")
    return render(request, "ordersapp/quote_list.html", {"quotes": quotes})


@require_http_methods(["GET", "POST"])
def quote_create(request):
    if request.method == "POST":
        form = QuoteForm(request.POST)
        formset = QuoteItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                quote = form.save(commit=False)
                assign_shop(request, quote)
                quote.save()
                items = formset.save(commit=False)
                for item in items:
                    item.quote = quote
                    if item.menu_item and not item.unit_price:
                        item.unit_price = item.menu_item.price_per_portion
                    item.save()
                for obj in formset.deleted_objects:
                    obj.delete()
                quote.recalc_totals()
                quote.save(update_fields=["total_amount"])
            messages.success(request, "Quote created.")
            return redirect("quote_list")
        messages.error(request, "Please fix the errors below.")
    else:
        form = QuoteForm()
        formset = QuoteItemFormSet()
    return render(request, "ordersapp/quote_form.html", {"form": form, "formset": formset, "is_edit": False})


@require_http_methods(["GET", "POST"])
def quote_update(request, quote_id):
    quote = tenant_get_object_or_404(request, Quote.objects.all(), id=quote_id)
    if request.method == "POST":
        form = QuoteForm(request.POST, instance=quote)
        formset = QuoteItemFormSet(request.POST, instance=quote)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                quote = form.save(commit=False)
                assign_shop(request, quote)
                quote.save()
                items = formset.save(commit=False)
                for item in items:
                    item.quote = quote
                    if item.menu_item and not item.unit_price:
                        item.unit_price = item.menu_item.price_per_portion
                    item.save()
                for obj in formset.deleted_objects:
                    obj.delete()
                quote.recalc_totals()
                quote.save(update_fields=["total_amount"])
            messages.success(request, "Quote updated.")
            return redirect("quote_list")
        messages.error(request, "Please fix the errors below.")
    else:
        form = QuoteForm(instance=quote)
        formset = QuoteItemFormSet(instance=quote)
    return render(request, "ordersapp/quote_form.html", {"form": form, "formset": formset, "is_edit": True, "quote": quote})


@require_http_methods(["GET"])
def quote_detail(request, quote_id):
    quote = tenant_get_object_or_404(request, Quote.objects.select_related("event", "event__customer"), id=quote_id)
    items = quote.items.select_related("menu_item")
    return render(request, "ordersapp/quote_detail.html", {"quote": quote, "items": items})


# -----------------------
# Revenue Reports
# -----------------------
def revenue_report(request):
    period = request.GET.get("period", "day")  # day, week, month
    start_raw = request.GET.get("start")
    end_raw = request.GET.get("end")
    start = parse_date(start_raw) if start_raw else None
    end = parse_date(end_raw) if end_raw else None
    qs = tenant_queryset(request, Order.objects.all())
    if start:
        qs = qs.filter(order_date__gte=start)
    if end:
        qs = qs.filter(order_date__lte=end)

    buckets = {}
    for o in qs:
        if period == "week":
            key = f"{o.order_date.isocalendar().year}-W{o.order_date.isocalendar().week:02d}"
            label = key
        elif period == "month":
            key = o.order_date.strftime("%Y-%m")
            label = key
        else:
            key = o.order_date.isoformat()
            label = key
        if key not in buckets:
            buckets[key] = {"label": label, "total": Decimal("0.00"), "received": Decimal("0.00")}
        buckets[key]["total"] += o.total_amount or Decimal("0.00")
        buckets[key]["received"] += o.received_amount or Decimal("0.00")

    rows = []
    for key, data in sorted(buckets.items()):
        due = data["total"] - data["received"]
        rows.append({
            "bucket": data["label"],
            "total": data["total"],
            "received": data["received"],
            "due": due,
        })

    totals = {
        "total": sum([r["total"] for r in rows], Decimal("0.00")),
        "received": sum([r["received"] for r in rows], Decimal("0.00")),
        "due": sum([r["due"] for r in rows], Decimal("0.00")),
    }

    return render(request, "ordersapp/revenue_report.html", {
        "rows": rows,
        "period": period,
        "start": start_raw,
        "end": end_raw,
        "totals": totals,
    })


def profit_loss_report(request):
    """Monthly P&L: revenue - stock usage cost - expenses."""
    start_raw = request.GET.get("start")
    end_raw = request.GET.get("end")
    start = parse_date(start_raw) if start_raw else None
    end = parse_date(end_raw) if end_raw else None

    # Revenue
    orders = tenant_queryset(request, Order.objects.all())
    if start:
        orders = orders.filter(order_date__gte=start)
    if end:
        orders = orders.filter(order_date__lte=end)

    # Stock usage cost (OUT movements)
    usage = StockMovement.objects.filter(movement_type=StockMovement.OUT).select_related("inventory_item")
    if not request.user.is_superuser and getattr(request, "shop", None):
        usage = usage.filter(inventory_item__shop=request.shop)
    if start:
        usage = usage.filter(created_at__date__gte=start)
    if end:
        usage = usage.filter(created_at__date__lte=end)

    # Expenses
    expenses = tenant_queryset(request, Expense.objects.all())
    if start:
        expenses = expenses.filter(date__gte=start)
    if end:
        expenses = expenses.filter(date__lte=end)

    buckets = {}

    def month_key(d):
        return d.strftime("%Y-%m")

    for o in orders:
        key = month_key(o.order_date)
        buckets.setdefault(key, {"revenue": Decimal("0.00"), "usage": Decimal("0.00"), "expenses": Decimal("0.00")})
        buckets[key]["revenue"] += o.total_amount or Decimal("0.00")

    for mv in usage:
        key = month_key(mv.created_at.date())
        buckets.setdefault(key, {"revenue": Decimal("0.00"), "usage": Decimal("0.00"), "expenses": Decimal("0.00")})
        unit_cost = mv.inventory_item.price_per_unit or Decimal("0.00")
        cost = (unit_cost * Decimal(mv.quantity)).quantize(Decimal("0.01"))
        buckets[key]["usage"] += cost

    for exp in expenses:
        key = month_key(exp.date)
        buckets.setdefault(key, {"revenue": Decimal("0.00"), "usage": Decimal("0.00"), "expenses": Decimal("0.00")})
        buckets[key]["expenses"] += exp.amount or Decimal("0.00")

    rows = []
    for key in sorted(buckets.keys()):
        data = buckets[key]
        profit = data["revenue"] - data["usage"] - data["expenses"]
        rows.append({
            "bucket": key,
            "revenue": data["revenue"],
            "usage": data["usage"],
            "expenses": data["expenses"],
            "profit": profit,
        })

    totals = {
        "revenue": sum([r["revenue"] for r in rows], Decimal("0.00")),
        "usage": sum([r["usage"] for r in rows], Decimal("0.00")),
        "expenses": sum([r["expenses"] for r in rows], Decimal("0.00")),
    }
    totals["profit"] = totals["revenue"] - totals["usage"] - totals["expenses"]

    return render(request, "ordersapp/profit_loss_report.html", {
        "rows": rows,
        "start": start_raw,
        "end": end_raw,
        "totals": totals,
    })


# -----------------------
# Create Order View
# -----------------------
@require_http_methods(["GET", "POST"])
def create_order(request):
    if request.method == "POST":
        order_date = safe_date(request.POST.get("order_date")) or timezone.localdate()
        customer_name = (request.POST.get("customer_name") or "").strip()
        address = (request.POST.get("address") or "").strip()
        try:
            phone_number = clean_phone(request.POST.get("phone_number"))
        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, "ordersapp/create_orders.html", order_form_context(request, is_edit=False))
        location = (request.POST.get("location") or "").strip()
        delivery_date = safe_date(request.POST.get("delivery_date"))
        delivery_time = safe_time(request.POST.get("delivery_time"))
        catering_date = safe_date(request.POST.get("catering_date")) or delivery_date
        catering_time = safe_time(request.POST.get("catering_time"))
        cnic_number = (request.POST.get("cnic") or "").strip()
        email = (request.POST.get("email") or "").strip()
        event_id = request.POST.get("event_id")
        gross_amount = safe_decimal(
            request.POST.get("gross_amount") or request.POST.get("total_amount"),
            "0.00",
        )
        discount_amount = safe_decimal(request.POST.get("discount_amount"), "0.00")
        discount_amount, total_amount = calculate_discounted_total(gross_amount, discount_amount)
        received_now = safe_decimal(request.POST.get("received_amount"), "0.00")

        # Parse item selections
        item_ids = request.POST.getlist("item_ids[]")
        quantities = request.POST.getlist("quantities[]")
        item_notes = request.POST.getlist("item_notes[]")
        parsed_rows = []
        for i, iid in enumerate(item_ids or []):
            try:
                q = int((quantities[i] if i < len(quantities) else "0") or "0")
            except (ValueError, TypeError):
                q = 0
            if not iid or q <= 0:
                continue
            note = item_notes[i] if i < len(item_notes) else ""
            parsed_rows.append((int(iid), q, note))

        # Menu item selections
        menu_ids = request.POST.getlist("menu_item_ids[]")
        menu_quantities = request.POST.getlist("menu_quantities[]")
        menu_notes = request.POST.getlist("menu_notes[]")
        menu_rows = []
        for i, mid in enumerate(menu_ids or []):
            try:
                q = int((menu_quantities[i] if i < len(menu_quantities) else "0") or "0")
            except (ValueError, TypeError):
                q = 0
            if not mid or q <= 0:
                continue
            note = menu_notes[i] if i < len(menu_notes) else ""
            menu_rows.append((int(mid), q, note))

        # Basic validation
        if gross_amount < 0:
            messages.error(request, "Subtotal cannot be negative.")
            return render(request, "ordersapp/create_orders.html", order_form_context(request, is_edit=False))

        # Must have at least one sellable menu item.
        if not parsed_rows and not menu_rows:
            messages.error(request, "Please add at least one menu item with quantity.")
            return render(request, "ordersapp/create_orders.html", order_form_context(request, is_edit=False))

        received_now = clamp_received(total_amount, received_now)

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    order_date=order_date,
                    customer_name=customer_name,
                    address=address,
                    phone_number=phone_number,
                    location=location,
                    delivery_date=delivery_date,
                    delivery_time=delivery_time,
                    catering_date=catering_date,
                    catering_time=catering_time,
                    total_amount=total_amount,
                    discount_amount=discount_amount,
                    received_amount=received_now,
                    cnic_number=cnic_number,
                    customer_type=(request.POST.get("customer_type") or "regular"),
                    email=email,
                    event_id=event_id or None,
                )
                assign_shop(request, order)
                order.save(update_fields=["shop"])
                save_customer_from_order_data(request, customer_name, phone_number, email, address, cnic_number)

                # Validate stock availability and create order items
                # Note: we only deduct on delivery, but we can prevent overbooking here
                inv_map = {
                    obj.id: obj
                    for obj in tenant_queryset(request, InventoryItem.objects.filter(id__in=[iid for iid, _, _ in parsed_rows]))
                }
                for iid, q, _note in parsed_rows:
                    inv = inv_map.get(iid)
                    if not inv:
                        raise ValueError("Invalid inventory item selected.")
                    if q > inv.quantity:
                        raise ValueError(f"Insufficient stock for {inv.name}. Requested {q}, available {inv.quantity}.")

                if parsed_rows:
                    OrderItem.objects.bulk_create([
                        OrderItem(order=order, inventory_item_id=iid, quantity=q, note=note)
                        for iid, q, note in parsed_rows
                    ])
                if menu_rows:
                    OrderMenuItem.objects.bulk_create([
                        OrderMenuItem(order=order, menu_item_id=mid, quantity=q, note=note)
                        for mid, q, note in menu_rows
                    ])

                # If any cash received at creation time, log a Payment row too
                if received_now > 0:
                    Payment.objects.create(order=order, amount=received_now)

            messages.success(request, "Order created. Invoice is ready.")
            return redirect("order_invoice", order_id=order.id)

        except Exception as e:
            messages.error(request, f"Could not create order: {e}")
            return render(request, "ordersapp/create_orders.html", order_form_context(request, is_edit=False))

    # GET
    return render(request, "ordersapp/create_orders.html", order_form_context(request, is_edit=False))


@require_http_methods(["POST"])
def quick_create_menu_item(request):
    name = (request.POST.get("name") or "").strip()
    category_id = request.POST.get("category") or ""
    price = safe_decimal(request.POST.get("price_per_portion"), "0.00")
    pricing_unit = request.POST.get("pricing_unit") or MenuItem.UNIT_HEAD
    note = (request.POST.get("note") or "").strip()

    if not name:
        return JsonResponse({"ok": False, "error": "Menu item name is required."}, status=400)
    if price < 0:
        return JsonResponse({"ok": False, "error": "Price cannot be negative."}, status=400)
    valid_units = {choice[0] for choice in MenuItem.PRICING_UNIT_CHOICES}
    if pricing_unit not in valid_units:
        return JsonResponse({"ok": False, "error": "Invalid pricing unit."}, status=400)

    category = None
    if category_id:
        category = tenant_get_object_or_404(request, MenuCategory.objects.all(), id=category_id)

    try:
        item = MenuItem(
            name=name,
            category=category,
            price_per_portion=price,
            pricing_unit=pricing_unit,
            description=note,
            is_active=True,
            needs_attention=True,
        )
        assign_shop(request, item)
        item.save()
    except Exception as exc:
        return JsonResponse({"ok": False, "error": f"Could not create menu item: {exc}"}, status=400)

    return JsonResponse(
        {
            "ok": True,
            "item": {
                "id": item.id,
                "name": item.name,
                "label": f"{item.name} ({item.get_pricing_unit_display()})",
            },
        }
    )


@require_http_methods(["POST"])
def quick_create_inventory_item(request):
    name = (request.POST.get("name") or "").strip()
    category_id = request.POST.get("category")
    uom_id = request.POST.get("uom")
    quantity_raw = request.POST.get("quantity") or "1"
    price_raw = request.POST.get("price_per_unit") or "0.00"
    supplier_name = (request.POST.get("supplier_name") or "Manual order entry").strip()
    description = (request.POST.get("description") or "").strip()

    if not name:
        return JsonResponse({"ok": False, "error": "Item name is required."}, status=400)

    try:
        quantity = int(quantity_raw)
    except (TypeError, ValueError):
        quantity = 0

    price_per_unit = safe_decimal(price_raw, "0.00")
    if quantity <= 0:
        return JsonResponse({"ok": False, "error": "Quantity must be greater than zero."}, status=400)
    if price_per_unit < 0:
        return JsonResponse({"ok": False, "error": "Price cannot be negative."}, status=400)

    category = get_object_or_404(InventoryCategory, id=category_id)
    uom = get_object_or_404(UnitOfMeasure, id=uom_id)
    total_amount = (price_per_unit * Decimal(quantity)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    try:
        with transaction.atomic():
            item = InventoryItem.objects.create(
                name=name,
                category=category,
                quantity=quantity,
                price_per_unit=price_per_unit,
                uom=uom,
                description=description,
                supplier_name=supplier_name,
                supplier_phone="",
                supplier_cnic="",
                supplier_address="",
                total_amount=total_amount,
                paid_amount=Decimal("0.00"),
                payment_method="cash",
            )
            assign_shop(request, item)
            item.save(update_fields=["shop"])
            StockMovement.objects.create(
                inventory_item=item,
                movement_type=StockMovement.IN,
                quantity=quantity,
                note="Quick added from order screen",
            )
    except Exception as exc:
        return JsonResponse({"ok": False, "error": f"Could not create item: {exc}"}, status=400)

    return JsonResponse(
        {
            "ok": True,
            "item": {
                "id": item.id,
                "name": item.name,
                "quantity": item.quantity,
                "label": f"{item.name} (avail: {item.quantity})",
            },
        }
    )


# -----------------------
# List Orders View
# -----------------------
@require_http_methods(["GET"])
def list_orders(request):
    orders = tenant_queryset(request, Order.objects.all()).order_by("-id")
    return render(request, "ordersapp/list_orders.html", {"orders": orders})


@require_http_methods(["GET"])
def order_invoice(request, order_id):
    order = tenant_get_object_or_404(
        request,
        Order.objects.select_related("shop", "event").prefetch_related(
            "menu_items__menu_item",
            "items__inventory_item",
            "payments",
        ),
        id=order_id,
    )
    shop = order.shop or getattr(request, "shop", None)
    invoice_shop_name = ""
    if shop:
        invoice_shop_name = shop.invoice_shop_name.strip() or shop.name

    rows = []
    for line in order.menu_items.select_related("menu_item"):
        unit_price = money(line.menu_item.price_per_portion)
        quantity = Decimal(line.quantity)
        rows.append(
            {
                "name": line.menu_item.name,
                "unit": line.menu_item.get_pricing_unit_display(),
                "quantity": line.quantity,
                "unit_price": unit_price,
                "line_total": money(unit_price * quantity),
                "note": line.note,
            }
        )

    for line in order.items.select_related("inventory_item"):
        unit_price = money(line.inventory_item.price_per_unit)
        quantity = Decimal(line.quantity)
        rows.append(
            {
                "name": line.inventory_item.name,
                "unit": "Inventory item",
                "quantity": line.quantity,
                "unit_price": unit_price,
                "line_total": money(unit_price * quantity),
                "note": line.note,
            }
        )

    payments = order.payments.order_by("payment_date", "id")
    return render(
        request,
        "ordersapp/order_invoice.html",
        {
            "order": order,
            "shop": shop,
            "invoice_shop_name": invoice_shop_name,
            "rows": rows,
            "payments": payments,
        },
    )


# -----------------------
# Payment Entry View
# -----------------------
@require_http_methods(["GET", "POST"])
def payment_entry(request, order_id):
    order = tenant_get_object_or_404(request, Order.objects.all(), id=order_id)

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
    orders = tenant_queryset(request, Order.objects.all()).order_by("-id")
    return render(request, "ordersapp/payment_entry_select.html", {"orders": orders})


# -----------------------
# Edit Order View (reuses create_orders.html)
# -----------------------
@require_http_methods(["GET", "POST"])
def edit_order(request, order_id):
    order = tenant_get_object_or_404(request, Order.objects.all(), id=order_id)

    if request.method == "POST":
        order.order_date = safe_date(request.POST.get("order_date")) or order.order_date or timezone.localdate()
        order.customer_name = (request.POST.get("customer_name") or "").strip()
        order.address = (request.POST.get("address") or "").strip()
        try:
            order.phone_number = clean_phone(request.POST.get("phone_number"))
        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, "ordersapp/create_orders.html", order_form_context(request, order=order, is_edit=True))
        order.location = (request.POST.get("location") or "").strip()
        order.delivery_date = safe_date(request.POST.get("delivery_date"))
        order.delivery_time = safe_time(request.POST.get("delivery_time"))
        order.catering_date = safe_date(request.POST.get("catering_date")) or order.delivery_date
        order.catering_time = safe_time(request.POST.get("catering_time"))
        order.cnic_number = (request.POST.get("cnic") or "").strip()
        order.customer_type = (request.POST.get("customer_type") or "regular")
        order.email = (request.POST.get("email") or "").strip()
        order.event_id = request.POST.get("event_id") or None

        current_gross = order.gross_amount if hasattr(order, "gross_amount") else (order.total_amount or Decimal("0.00"))
        gross_amount = safe_decimal(
            request.POST.get("gross_amount") or request.POST.get("total_amount"),
            str(current_gross),
        )
        discount_amount = safe_decimal(request.POST.get("discount_amount"), str(order.discount_amount or "0.00"))
        discount_amount, new_total = calculate_discounted_total(gross_amount, discount_amount)
        new_received = safe_decimal(request.POST.get("received_amount"), str(order.received_amount or "0.00"))

        if gross_amount < 0:
            messages.error(request, "Subtotal cannot be negative.")
            return render(request, "ordersapp/create_orders.html", order_form_context(request, order=order, is_edit=True))

        item_ids = request.POST.getlist("item_ids[]")
        quantities = request.POST.getlist("quantities[]")
        item_notes = request.POST.getlist("item_notes[]")
        parsed_rows = []
        for i, iid in enumerate(item_ids or []):
            try:
                q = int((quantities[i] if i < len(quantities) else "0") or "0")
            except (ValueError, TypeError):
                q = 0
            if not iid or q <= 0:
                continue
            note = item_notes[i] if i < len(item_notes) else ""
            parsed_rows.append((int(iid), q, note))

        menu_ids = request.POST.getlist("menu_item_ids[]")
        menu_quantities = request.POST.getlist("menu_quantities[]")
        menu_notes = request.POST.getlist("menu_notes[]")
        menu_rows = []
        for i, mid in enumerate(menu_ids or []):
            try:
                q = int((menu_quantities[i] if i < len(menu_quantities) else "0") or "0")
            except (ValueError, TypeError):
                q = 0
            if not mid or q <= 0:
                continue
            note = menu_notes[i] if i < len(menu_notes) else ""
            menu_rows.append((int(mid), q, note))

        if not parsed_rows and not menu_rows:
            messages.error(request, "Please add at least one menu item with quantity.")
            return render(request, "ordersapp/create_orders.html", order_form_context(request, order=order, is_edit=True))

        # Normalize received vs total
        new_received = clamp_received(new_total, new_received)

        order.total_amount = new_total
        order.discount_amount = discount_amount
        order.received_amount = new_received

        try:
            with transaction.atomic():
                inv_map = {
                    obj.id: obj
                    for obj in tenant_queryset(request, InventoryItem.objects.filter(id__in=[iid for iid, _, _ in parsed_rows]))
                }
                for iid, q, _note in parsed_rows:
                    inv = inv_map.get(iid)
                    if not inv:
                        raise ValueError("Invalid inventory item selected.")
                    if q > inv.quantity:
                        raise ValueError(f"Insufficient stock for {inv.name}. Requested {q}, available {inv.quantity}.")

                order.save()
                save_customer_from_order_data(
                    request,
                    order.customer_name,
                    order.phone_number,
                    order.email,
                    order.address,
                    order.cnic_number,
                )
                order.items.all().delete()
                order.menu_items.all().delete()
                if parsed_rows:
                    OrderItem.objects.bulk_create([
                        OrderItem(order=order, inventory_item_id=iid, quantity=q, note=note)
                        for iid, q, note in parsed_rows
                    ])
                if menu_rows:
                    OrderMenuItem.objects.bulk_create([
                        OrderMenuItem(order=order, menu_item_id=mid, quantity=q, note=note)
                        for mid, q, note in menu_rows
                    ])
            messages.success(request, "✅ Order updated successfully.")
            return redirect("order_invoice", order_id=order.id)
        except Exception as e:
            messages.error(request, f"Could not update order: {e}")

    # GET
    return render(
        request,
        "ordersapp/create_orders.html",
        order_form_context(request, order=order, is_edit=True),
    )


# -----------------------
# Delete Order View
# -----------------------
@require_http_methods(["GET", "POST"])
def delete_order(request, order_id):
    order = tenant_get_object_or_404(request, Order.objects.all(), id=order_id)

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
    order = tenant_get_object_or_404(request, Order.objects.all(), id=order_id)

    if order.status == Order.STATUS_DELIVERED:
        messages.info(request, "Order already delivered.")
        return redirect("list_orders")

    items = list(order.items.select_related("inventory_item").all())
    menu_items = list(order.menu_items.select_related("menu_item").all())
    if not items:
        # allow menu-only orders if recipes exist
        if not menu_items:
            messages.error(request, "No items found for this order. Add items before delivering.")
            return redirect("list_orders")

    try:
        with transaction.atomic():
            # Aggregate required inventory from direct items and menu recipes
            required = {}

            # From direct inventory order items
            for oi in items:
                required[oi.inventory_item_id] = required.get(oi.inventory_item_id, 0) + oi.quantity

            # From menu items via recipe
            if menu_items:
                recipe_rows = RecipeItem.objects.filter(menu_item__in=[m.menu_item_id for m in menu_items]).select_related("inventory_item")
                recipe_map = {}
                for r in recipe_rows:
                    recipe_map.setdefault(r.menu_item_id, []).append(r)
                for m in menu_items:
                    recipes = recipe_map.get(m.menu_item_id, [])
                    for r in recipes:
                        need = (r.quantity_per_portion or Decimal("0")) * Decimal(m.quantity)
                        required[r.inventory_item_id] = required.get(r.inventory_item_id, Decimal("0")) + need

            # Validate stock availability first
            if required:
                inv_map = {inv.id: inv for inv in InventoryItem.objects.filter(id__in=required.keys())}
                for inv_id, qty in required.items():
                    inv = inv_map.get(inv_id)
                    if not inv:
                        raise ValueError("Inventory item not found for deduction.")
                    if Decimal(qty) > inv.quantity:
                        raise ValueError(f"Insufficient stock for {inv.name}. Needed {qty}, available {inv.quantity}.")

                # Deduct stock
                for inv_id, qty in required.items():
                    InventoryItem.objects.filter(id=inv_id).update(
                        quantity=F("quantity") - qty
                    )
                    StockMovement.objects.create(
                        inventory_item_id=inv_id,
                        movement_type=StockMovement.OUT,
                        quantity=qty,
                        note=f"Order {order.id} delivery",
                    )

            # Mark order delivered
            order.status = Order.STATUS_DELIVERED
            order.delivered_at = timezone.now()
            order.save(update_fields=["status", "delivered_at"])

        messages.success(request, "✅ Order delivered and stock updated.")
    except Exception as e:
        messages.error(request, f"Could not deliver order: {e}")

    return redirect("list_orders")
