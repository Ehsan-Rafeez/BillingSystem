from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from .models import InventoryItem, UnitOfMeasure
from decimal import Decimal


def add_stock(request):
    """Add new stock item."""
    uoms = UnitOfMeasure.objects.all().order_by("name")

    if request.method == "POST":
        try:
            name = request.POST.get("name")
            category = request.POST.get("category")
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

            uom = get_object_or_404(UnitOfMeasure, id=uom_id)

            InventoryItem.objects.create(
                name=name,
                category=category,
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
        "categories": InventoryItem.CATEGORY_CHOICES,
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

    if status == "paid":
        stocks = [s for s in stocks if s.paid_amount >= s.total_amount]
    elif status == "pending":
        stocks = [s for s in stocks if 0 < s.paid_amount < s.total_amount]
    elif status == "unpaid":
        stocks = [s for s in stocks if s.paid_amount == 0]

    return render(request, "inventory/list_stock.html", {
        "stocks": stocks,
        "query": query,
        "status": status,
    })


def edit_stock(request, pk):
    """Edit stock item (same template as add_stock)."""
    stock = get_object_or_404(InventoryItem, pk=pk)
    uoms = UnitOfMeasure.objects.all().order_by("name")

    if request.method == "POST":
        try:
            stock.name = request.POST.get("name")
            stock.category = request.POST.get("category")
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
        "categories": InventoryItem.CATEGORY_CHOICES,
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
