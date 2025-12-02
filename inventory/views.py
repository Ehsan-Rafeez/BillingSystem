import csv
from datetime import timedelta, datetime, time

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, F
from django.contrib import messages
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from django.utils import timezone
from decimal import Decimal
from collections import defaultdict
from .models import InventoryItem, UnitOfMeasure, InventoryCategory, InventoryBaseItem, StockMovement
from .forms import InventoryBaseItemForm, UnitOfMeasureForm, InventoryCategoryForm
from suppliers.models import Supplier


# ---- Utility: Add default Units of Measure if none exist ----
def load_default_uoms():
    defaults = [
        {"name": "Kilogram", "abbreviation": "kg"},
        {"name": "Gram", "abbreviation": "g"},
        {"name": "Liter", "abbreviation": "L"},
        {"name": "Milliliter", "abbreviation": "ml"},
        {"name": "Piece", "abbreviation": "pc"},
        {"name": "Box", "abbreviation": "box"},
    ]
    if UnitOfMeasure.objects.count() == 0:  # only load if empty
        for d in defaults:
            UnitOfMeasure.objects.create(name=d["name"], abbreviation=d["abbreviation"])


# ---- Utility: Add default Categories if none exist ----
def load_default_categories():
    defaults = [
        "Fruits & Vegetables",
        "Dairy & Eggs",
        "Meat & Poultry",
        "Bakery & Breads",
        "Pantry Staples",
        "Beverages",
        "Snacks & Packaged Foods",
        "Frozen Foods",
        "Canned & Jarred Goods",
        "Health & Personal Care",
        "Household Essentials",
        "Baby Products",
        "Pet Food & Supplies",
    ]
    if InventoryCategory.objects.count() == 0:  # only load if empty
        for name in defaults:
            InventoryCategory.objects.create(name=name)


# ---------------- STOCK VIEWS ---------------- #

def add_stock(request):
    """Add new stock item."""
    load_default_uoms()        # ensure UOMs exist
    load_default_categories()  # ensure Categories exist
    uoms = UnitOfMeasure.objects.all().order_by("name")
    categories = InventoryCategory.objects.all().order_by("name")
    suppliers = Supplier.objects.filter(is_active=True).order_by("name")

    if request.method == "POST":
        try:
            name = request.POST.get("name")
            category_id = request.POST.get("category")
            quantity = int(request.POST.get("quantity", 1))
            price_per_unit = Decimal(request.POST.get("price_per_unit", 0))
            uom_id = request.POST.get("uom")
            description = request.POST.get("description")

            supplier_name = request.POST.get("supplier_name")
            supplier_phone = request.POST.get("supplier_phone")
            supplier_cnic = request.POST.get("supplier_cnic")
            supplier_address = request.POST.get("supplier_address")

            total_amount = Decimal(request.POST.get("total_amount", 0))
            paid_amount = Decimal(request.POST.get("paid_amount", 0))
            payment_method = request.POST.get("payment_method")

            if paid_amount > total_amount:
                messages.error(request, "Paid amount cannot exceed total amount.")
                raise ValueError("Invalid payment amounts")

            rent_price = request.POST.get("rent_price") or None
            rent_type = request.POST.get("rent_type") or None
            rent_condition = request.POST.get("rent_condition") or None

            category = get_object_or_404(InventoryCategory, id=category_id)
            uom = get_object_or_404(UnitOfMeasure, id=uom_id)

            stock = InventoryItem.objects.create(
                name=name,
                category=category,   # ✅ save FK not name
                quantity=quantity,
                price_per_unit=price_per_unit,
                uom=uom,
                description=description,
                supplier_name=supplier_name,
                supplier_phone=supplier_phone,
                supplier_cnic=supplier_cnic,
                supplier_address=supplier_address,
                total_amount=total_amount,
                paid_amount=paid_amount,
                payment_method=payment_method,
                rent_price=rent_price,
                rent_type=rent_type,
                rent_condition=rent_condition,
            )
            # Log movement for initial stock
            StockMovement.objects.create(
                inventory_item=stock,
                movement_type=StockMovement.IN,
                quantity=quantity,
                note="Initial stock entry",
            )

            messages.success(request, f"Stock '{name}' added successfully!")
            return redirect("list_stock")

        except Exception as e:
            messages.error(request, f"Error adding stock: {str(e)}")

    return render(request, "inventory/add_stock.html", {
        "uoms": uoms,
        "categories": categories,
        "suppliers": suppliers,
        "is_edit": False,
    })


def list_stock(request):
    """List all stock items with filters and search."""
    query = request.GET.get("q")
    status = request.GET.get("status")

    stocks = InventoryItem.objects.all().order_by("-created_at")

    if query:
        stocks = stocks.filter(
            Q(stock_code__icontains=query) |
            Q(name__icontains=query) |
            Q(supplier_name__icontains=query) |
            Q(description__icontains=query)
        )

    # Add calculated fields for each stock
    stock_list = []
    for s in stocks:
        remaining = s.total_amount - s.paid_amount
        if s.paid_amount >= s.total_amount:
            payment_status = "Paid"
        elif s.paid_amount == 0:
            payment_status = "Unpaid"
        else:
            payment_status = "Pending"

        stock_list.append({
            "id": s.id,
            "stock_code": getattr(s, "stock_code", f"STK-{s.id:04}"),
            "name": s.name,
            "category": s.category.name if s.category else "",   # ✅ show category name
            "quantity": s.quantity,
            "min_quantity": getattr(s, "min_quantity", 0),
            "uom": s.uom,
            "total_amount": s.total_amount,
            "paid_amount": s.paid_amount,
            "remaining_amount": remaining,
            "status": payment_status,
            "payment_method": s.get_payment_method_display() if hasattr(s, "get_payment_method_display") else s.payment_method,
            "supplier_name": s.supplier_name,
            "low_stock": s.quantity <= getattr(s, "min_quantity", 0),
        })

    # Apply filter
    if status == "paid":
        stock_list = [s for s in stock_list if s["status"] == "Paid"]
    elif status == "pending":
        stock_list = [s for s in stock_list if s["status"] == "Pending"]
    elif status == "unpaid":
        stock_list = [s for s in stock_list if s["status"] == "Unpaid"]

    return render(request, "inventory/list_stock.html", {
        "stocks": stock_list,
        "query": query,
        "status": status,
    })


def edit_stock(request, pk):
    """Edit stock item (same template as add_stock)."""
    stock = get_object_or_404(InventoryItem, pk=pk)
    old_qty = stock.quantity
    load_default_uoms()
    load_default_categories()
    uoms = UnitOfMeasure.objects.all().order_by("name")
    categories = InventoryCategory.objects.all().order_by("name")
    suppliers = Supplier.objects.filter(is_active=True).order_by("name")

    if request.method == "POST":
        try:
            stock.name = request.POST.get("name")
            category_id = request.POST.get("category")
            stock.category = get_object_or_404(InventoryCategory, id=category_id)
            stock.quantity = int(request.POST.get("quantity", 1))
            stock.price_per_unit = Decimal(request.POST.get("price_per_unit", 0))
            stock.uom = get_object_or_404(UnitOfMeasure, id=request.POST.get("uom"))
            stock.description = request.POST.get("description")

            stock.supplier_name = request.POST.get("supplier_name")
            stock.supplier_phone = request.POST.get("supplier_phone")
            stock.supplier_cnic = request.POST.get("supplier_cnic")
            stock.supplier_address = request.POST.get("supplier_address")

            stock.total_amount = Decimal(request.POST.get("total_amount", 0))
            stock.paid_amount = Decimal(request.POST.get("paid_amount", 0))
            stock.payment_method = request.POST.get("payment_method")

            if stock.paid_amount > stock.total_amount:
                messages.error(request, "Paid amount cannot exceed total amount.")
                raise ValueError("Invalid payment amounts")

            stock.rent_price = request.POST.get("rent_price") or None
            stock.rent_type = request.POST.get("rent_type") or None
            stock.rent_condition = request.POST.get("rent_condition") or None

            stock.save()
            # Log movement if quantity changed
            delta = stock.quantity - old_qty
            if delta != 0:
                StockMovement.objects.create(
                    inventory_item=stock,
                    movement_type=StockMovement.IN if delta > 0 else StockMovement.OUT,
                    quantity=abs(Decimal(delta)),
                    note="Manual edit adjustment",
                )
            messages.success(request, f"Stock '{stock.name}' updated successfully!")
            return redirect("list_stock")

        except Exception as e:
            messages.error(request, f"Error updating stock: {str(e)}")

    return render(request, "inventory/add_stock.html", {
        "stock": stock,
        "uoms": uoms,
        "categories": categories,
        "suppliers": suppliers,
        "is_edit": True,
    })


def delete_stock(request, pk):
    """Delete stock item."""
    stock = get_object_or_404(InventoryItem, pk=pk)
    stock.delete()
    messages.success(request, f"Stock '{stock.name}' deleted successfully!")
    return redirect("list_stock")


def add_payment(request, pk):
    """Add payment for a stock item."""
    stock = get_object_or_404(InventoryItem, pk=pk)

    if request.method == "POST":
        try:
            extra_payment = Decimal(request.POST.get("extra_payment", 0))
            stock.paid_amount += extra_payment
            stock.save()
            messages.success(request, f"Payment updated for '{stock.name}'.")
            return redirect("list_stock")
        except Exception as e:
            messages.error(request, f"Error adding payment: {str(e)}")

    return render(request, "inventory/add_payment.html", {"stock": stock})


def restock_item(request, pk):
    """Increment quantity for an existing stock item and log movement."""
    stock = get_object_or_404(InventoryItem, pk=pk)
    if request.method == "POST":
        try:
            qty = Decimal(request.POST.get("restock_quantity", "0"))
            note = (request.POST.get("note") or "").strip()
            if qty <= 0:
                messages.error(request, "Quantity must be greater than zero.")
                return redirect("restock_item", pk=pk)
            InventoryItem.objects.filter(id=stock.id).update(quantity=F("quantity") + qty)
            StockMovement.objects.create(
                inventory_item=stock,
                movement_type=StockMovement.IN,
                quantity=qty,
                note=note or "Restock",
            )
            messages.success(request, f"Restocked '{stock.name}' by {qty}.")
            return redirect("list_stock")
        except Exception as e:
            messages.error(request, f"Error restocking: {e}")
    return render(request, "inventory/restock_item.html", {"stock": stock})


# ---------------- INVENTORY VIEWS ---------------- #

def add_inventory(request):
    """Add new inventory item with categories & UOMs from DB"""
    load_default_categories()  # ensure Categories exist
    load_default_uoms()        # ensure UOMs exist
    categories = InventoryCategory.objects.all().order_by("name")
    uoms = UnitOfMeasure.objects.all().order_by("name")

    if request.method == "POST":
        try:
            name = request.POST.get("name")
            category_id = request.POST.get("category")
            uom_id = request.POST.get("uom")
            quantity = int(request.POST.get("quantity", 1))
            price_per_unit = Decimal(request.POST.get("price_per_unit", 0))
            description = request.POST.get("description")

            category = get_object_or_404(InventoryCategory, id=category_id)
            uom = get_object_or_404(UnitOfMeasure, id=uom_id)

            InventoryItem.objects.create(
                name=name,
                category=category,   # ✅ save FK directly
                uom=uom,
                quantity=quantity,
                price_per_unit=price_per_unit,
                description=description,
                total_amount=price_per_unit * quantity,
                paid_amount=Decimal(0)
            )

            messages.success(request, f"Inventory item '{name}' added successfully!")
            return redirect("list_inventory")

        except Exception as e:
            messages.error(request, f"Error adding inventory item: {str(e)}")

    return render(request, "inventory/add_inventory.html", {
        "categories": categories,
        "uoms": uoms,
    })


def list_inventory(request):
    """List all inventory items"""
    items = InventoryItem.objects.all().order_by("-created_at")
    return render(request, "inventory/list_inventory.html", {"items": items})


# ---------------- LIVE STOCK VIEW ---------------- #

def live_stock(request):
    """
    Show combined live stock (Stock + Inventory).
    If same item name exists, quantities will be summed.
    """
    combined = defaultdict(int)

    # Collect all inventory items (both stock and inventory)
    items = InventoryItem.objects.all()

    for item in items:
        combined[item.name] += item.quantity

    # Convert dict into list of dicts for template
    live_items = [{"name": k, "quantity": v} for k, v in combined.items()]

    return render(request, "inventory/live_stock.html", {"live_items": live_items})


# ---------------- BASE INVENTORY (catalog) ---------------- #
def base_item_list(request):
    items = InventoryBaseItem.objects.select_related("uom", "supplier").order_by("name")
    return render(request, "inventory/baseitem_list.html", {"items": items})


def base_item_create(request):
    if request.method == "POST":
        form = InventoryBaseItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Base item created.")
            return redirect("baseitem_list")
        messages.error(request, "Please fix the errors below.")
    else:
        form = InventoryBaseItemForm()
    return render(request, "inventory/baseitem_form.html", {"form": form, "is_edit": False})


def base_item_update(request, pk):
    item = get_object_or_404(InventoryBaseItem, pk=pk)
    if request.method == "POST":
        form = InventoryBaseItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Base item updated.")
            return redirect("baseitem_list")
        messages.error(request, "Please fix the errors below.")
    else:
        form = InventoryBaseItemForm(instance=item)
    return render(request, "inventory/baseitem_form.html", {"form": form, "is_edit": True, "item": item})


def base_item_delete(request, pk):
    item = get_object_or_404(InventoryBaseItem, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Base item deleted.")
        return redirect("baseitem_list")
    return render(request, "inventory/baseitem_confirm_delete.html", {"item": item})


# ---------------- UOM & CATEGORY MGMT ---------------- #
def uom_list(request):
    uoms = UnitOfMeasure.objects.order_by("name")
    return render(request, "inventory/uom_list.html", {"uoms": uoms})


def uom_create(request):
    if request.method == "POST":
        form = UnitOfMeasureForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Unit created.")
            return redirect("uom_list")
        messages.error(request, "Please fix the errors below.")
    else:
        form = UnitOfMeasureForm()
    return render(request, "inventory/uom_form.html", {"form": form, "is_edit": False})


def uom_update(request, pk):
    uom = get_object_or_404(UnitOfMeasure, pk=pk)
    if request.method == "POST":
        form = UnitOfMeasureForm(request.POST, instance=uom)
        if form.is_valid():
            form.save()
            messages.success(request, "Unit updated.")
            return redirect("uom_list")
        messages.error(request, "Please fix the errors below.")
    else:
        form = UnitOfMeasureForm(instance=uom)
    return render(request, "inventory/uom_form.html", {"form": form, "is_edit": True, "uom": uom})


def category_list(request):
    categories = InventoryCategory.objects.order_by("name")
    return render(request, "inventory/category_list.html", {"categories": categories})


def category_create(request):
    if request.method == "POST":
        form = InventoryCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category created.")
            return redirect("inventory_category_list")
        messages.error(request, "Please fix the errors below.")
    else:
        form = InventoryCategoryForm()
    return render(request, "inventory/category_form.html", {"form": form, "is_edit": False})


def category_update(request, pk):
    category = get_object_or_404(InventoryCategory, pk=pk)
    if request.method == "POST":
        form = InventoryCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated.")
            return redirect("inventory_category_list")
        messages.error(request, "Please fix the errors below.")
    else:
        form = InventoryCategoryForm(instance=category)
    return render(request, "inventory/category_form.html", {"form": form, "is_edit": True, "category": category})


# ---------------- REPORTS ---------------- #
def _parse_date_any(val):
    if not val:
        return None
    # try ISO first
    d = parse_date(val)
    if d:
        return d
    for fmt in ("%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None


def stock_purchase_report(request):
    """Report on stock purchases/restocks with export."""
    start_raw = request.GET.get("start")
    end_raw = request.GET.get("end")
    download = request.GET.get("download")

    start = _parse_date_any(start_raw)
    end = _parse_date_any(end_raw)

    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.combine(start, time.min), tz) if start else None
    end_dt = timezone.make_aware(datetime.combine(end, time.max), tz) if end else None

    items_qs = InventoryItem.objects.all()
    if start_dt and end_dt:
        items_qs = items_qs.filter(created_at__range=(start_dt, end_dt))
    elif start_dt:
        items_qs = items_qs.filter(created_at__gte=start_dt)
    elif end_dt:
        items_qs = items_qs.filter(created_at__lte=end_dt)

    movements_qs = StockMovement.objects.filter(movement_type=StockMovement.IN).select_related("inventory_item")
    if start_dt and end_dt:
        movements_qs = movements_qs.filter(created_at__range=(start_dt, end_dt))
    elif start_dt:
        movements_qs = movements_qs.filter(created_at__gte=start_dt)
    elif end_dt:
        movements_qs = movements_qs.filter(created_at__lte=end_dt)

    rows = []
    for itm in items_qs:
        rows.append({
            "date": itm.created_at.date(),
            "item": itm.name,
            "category": itm.category.name if itm.category else "",
            "quantity": itm.quantity,
            "uom": itm.uom.abbreviation,
            "amount": itm.total_amount,
            "source": "New Stock",
            "note": itm.description or "",
        })
    for mv in movements_qs:
        rows.append({
            "date": mv.created_at.date(),
            "item": mv.inventory_item.name,
            "category": mv.inventory_item.category.name if mv.inventory_item.category else "",
            "quantity": mv.quantity,
            "uom": mv.inventory_item.uom.abbreviation,
            "amount": "",
            "source": "Restock",
            "note": mv.note,
        })

    # Sort by date
    rows = sorted(rows, key=lambda r: r["date"], reverse=True)

    if download == "csv":
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="stock_purchases.csv"'
        writer = csv.writer(resp)
        writer.writerow(["Date", "Item", "Category", "Quantity", "UOM", "Amount", "Source", "Note"])
        for r in rows:
            writer.writerow([r["date"], r["item"], r["category"], r["quantity"], r["uom"], r["amount"], r["source"], r["note"]])
        return resp

    # Simple rollups
    total_qty = sum([Decimal(r["quantity"]) for r in rows]) if rows else Decimal("0")
    total_amount = sum([Decimal(r["amount"]) for r in rows if r["amount"]]) if rows else Decimal("0")

    return render(request, "inventory/stock_purchase_report.html", {
        "rows": rows,
        "start": start_raw,
        "end": end_raw,
        "total_qty": total_qty,
        "total_amount": total_amount,
    })


def stock_usage_report(request):
    """Report on stock usage (OUT movements)."""
    start_raw = request.GET.get("start")
    end_raw = request.GET.get("end")
    start = _parse_date_any(start_raw)
    end = _parse_date_any(end_raw)
    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.combine(start, time.min), tz) if start else None
    end_dt = timezone.make_aware(datetime.combine(end, time.max), tz) if end else None

    qs = StockMovement.objects.filter(movement_type=StockMovement.OUT).select_related("inventory_item")
    if start_dt and end_dt:
        qs = qs.filter(created_at__range=(start_dt, end_dt))
    elif start_dt:
        qs = qs.filter(created_at__gte=start_dt)
    elif end_dt:
        qs = qs.filter(created_at__lte=end_dt)

    rows = []
    for mv in qs.order_by("-created_at"):
        rows.append({
            "date": mv.created_at.date(),
            "item": mv.inventory_item.name,
            "category": mv.inventory_item.category.name if mv.inventory_item.category else "",
            "quantity": mv.quantity,
            "uom": mv.inventory_item.uom.abbreviation,
            "note": mv.note,
        })

    total_qty = sum([Decimal(r["quantity"]) for r in rows]) if rows else Decimal("0")

    return render(request, "inventory/stock_usage_report.html", {
        "rows": rows,
        "start": start_raw,
        "end": end_raw,
        "total_qty": total_qty,
    })
