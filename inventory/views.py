from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from decimal import Decimal
from collections import defaultdict
from .models import InventoryItem, UnitOfMeasure, InventoryCategory


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

            rent_price = request.POST.get("rent_price") or None
            rent_type = request.POST.get("rent_type") or None
            rent_condition = request.POST.get("rent_condition") or None

            category = get_object_or_404(InventoryCategory, id=category_id)
            uom = get_object_or_404(UnitOfMeasure, id=uom_id)

            InventoryItem.objects.create(
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

            messages.success(request, f"Stock '{name}' added successfully!")
            return redirect("list_stock")

        except Exception as e:
            messages.error(request, f"Error adding stock: {str(e)}")

    return render(request, "inventory/add_stock.html", {
        "uoms": uoms,
        "categories": categories,
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
            "uom": s.uom,
            "total_amount": s.total_amount,
            "paid_amount": s.paid_amount,
            "remaining_amount": remaining,
            "status": payment_status,
            "payment_method": s.get_payment_method_display() if hasattr(s, "get_payment_method_display") else s.payment_method,
            "supplier_name": s.supplier_name,
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
    load_default_uoms()
    load_default_categories()
    uoms = UnitOfMeasure.objects.all().order_by("name")
    categories = InventoryCategory.objects.all().order_by("name")

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

            stock.rent_price = request.POST.get("rent_price") or None
            stock.rent_type = request.POST.get("rent_type") or None
            stock.rent_condition = request.POST.get("rent_condition") or None

            stock.save()
            messages.success(request, f"Stock '{stock.name}' updated successfully!")
            return redirect("list_stock")

        except Exception as e:
            messages.error(request, f"Error updating stock: {str(e)}")

    return render(request, "inventory/add_stock.html", {
        "stock": stock,
        "uoms": uoms,
        "categories": categories,
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
