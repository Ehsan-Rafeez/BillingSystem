from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum
from .models import Supplier, SupplierPayment, PurchaseOrder, PurchaseOrderItem
from .forms import SupplierForm, SupplierPaymentForm, PurchaseOrderForm
from inventory.models import InventoryItem


def supplier_list(request):
    """Display list of all suppliers"""
    suppliers = Supplier.objects.all().order_by('name')
    return render(request, 'suppliers/supplier_list.html', {'suppliers': suppliers})


def supplier_detail(request, supplier_id):
    """Display detailed view of a supplier with payments and purchase orders"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    payments = supplier.payments.all().order_by('-payment_date')
    purchase_orders = supplier.purchase_orders.all().order_by('-order_date')
    
    # Calculate summary statistics
    total_purchases = supplier.total_purchases
    total_paid = supplier.total_paid
    balance_due = supplier.balance_due
    
    context = {
        'supplier': supplier,
        'payments': payments,
        'purchase_orders': purchase_orders,
        'total_purchases': total_purchases,
        'total_paid': total_paid,
        'balance_due': balance_due,
    }
    return render(request, 'suppliers/supplier_detail.html', context)


def supplier_create(request):
    """Create a new supplier"""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'Supplier "{supplier.name}" created successfully!')
            return redirect('supplier_detail', supplier_id=supplier.id)
    else:
        form = SupplierForm()
    
    return render(request, 'suppliers/supplier_form.html', {
        'form': form,
        'title': 'Create New Supplier'
    })


def supplier_edit(request, supplier_id):
    """Edit an existing supplier"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f'Supplier "{supplier.name}" updated successfully!')
            return redirect('supplier_detail', supplier_id=supplier.id)
    else:
        form = SupplierForm(instance=supplier)
    
    return render(request, 'suppliers/supplier_form.html', {
        'form': form,
        'title': f'Edit {supplier.name}',
        'supplier': supplier
    })


def payment_create(request, supplier_id):
    """Create a new payment for a supplier"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    if request.method == 'POST':
        form = SupplierPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.supplier = supplier
            payment.save()
            messages.success(request, f'Payment of {payment.amount} recorded successfully!')
            return redirect('supplier_detail', supplier_id=supplier.id)
    else:
        form = SupplierPaymentForm()
    
    return render(request, 'suppliers/payment_form.html', {
        'form': form,
        'supplier': supplier,
        'title': f'Record Payment for {supplier.name}'
    })


def purchase_order_list(request):
    """Display list of all purchase orders"""
    purchase_orders = PurchaseOrder.objects.all().order_by('-order_date')
    return render(request, 'suppliers/purchase_order_list.html', {
        'purchase_orders': purchase_orders
    })


def purchase_order_detail(request, po_id):
    """Display detailed view of a purchase order"""
    purchase_order = get_object_or_404(PurchaseOrder, id=po_id)
    items = purchase_order.items.all()
    
    return render(request, 'suppliers/purchase_order_detail.html', {
        'purchase_order': purchase_order,
        'items': items
    })


def purchase_order_create(request):
    """Create a new purchase order"""
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            purchase_order = form.save()
            messages.success(request, f'Purchase Order {purchase_order.order_number} created successfully!')
            return redirect('purchase_order_detail', po_id=purchase_order.id)
    else:
        form = PurchaseOrderForm()
    
    return render(request, 'suppliers/purchase_order_form.html', {
        'form': form,
        'title': 'Create New Purchase Order'
    })