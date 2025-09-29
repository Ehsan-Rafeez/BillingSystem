from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import InventoryItem, UnitOfMeasure


# ✅ Add Stock
def add_stock(request):
    if request.method == "POST":
        # Form fields
        stock_name = request.POST.get("stock_name")
        category = request.POST.get("category")  # buy / rent / order
        quantity = request.POST.get("quantity")
        price_per_unit = request.POST.get("price_per_unit")
        rent_duration = request.POST.get("rent_duration")
        order_date = request.POST.get("order_date")

        # Dummy UOM
        uom, created = UnitOfMeasure.objects.get_or_create(
            name="Pieces", abbreviation="pcs"
        )

        # Save stock
        InventoryItem.objects.create(
            name=stock_name,
            description=f"{category} item",
            quantity=quantity or 0,
            item_type=InventoryItem.ASSET if category == "rent" else InventoryItem.RAW,
            uom=uom,
            price=price_per_unit or 0,
            cost_per_uom=price_per_unit or 0,
            qty_on_hand=quantity or 0,
            qty_available=quantity or 0,
        )

        messages.success(request, "✅ Stock item added successfully")
        return redirect("list_stock")

    return render(request, "inventory/add_stock.html")


# ✅ List Stock
def list_stock(request):
    stocks = InventoryItem.objects.all().order_by("-created_at")
    return render(request, "inventory/list_stock.html", {"stocks": stocks})


# ✅ Edit Stock
def edit_stock(request, pk):
    stock = get_object_or_404(InventoryItem, pk=pk)

    if request.method == "POST":
        stock.name = request.POST.get("stock_name")
        stock.category = request.POST.get("category")
        stock.description = request.POST.get("description")
        stock.price = request.POST.get("price_per_unit")
        stock.save()
        messages.success(request, "✏ Stock updated successfully")
        return redirect("list_stock")

    return render(request, "inventory/edit_stock.html", {"stock": stock})


# ✅ Delete Stock
def delete_stock(request, pk):
    stock = get_object_or_404(InventoryItem, pk=pk)
    stock.delete()
    messages.success(request, "🗑 Stock deleted successfully")
    return redirect("list_stock")


# ✅ Mark Returned (for Rent Items)
def mark_returned(request, pk):
    stock = get_object_or_404(InventoryItem, pk=pk)
    if stock.item_type == InventoryItem.ASSET:  # rent type
        stock.qty_available = stock.qty_on_hand
        stock.save()
        messages.success(request, "✔ Item marked as returned")
    return redirect("list_stock")
