# ordersapp/views.py

from decimal import Decimal, InvalidOperation

from django.db.models import F
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import ModelForm

from .models import Order, Payment


# -----------------------
# Create Order View
# -----------------------
def create_order(request):
    if request.method == 'POST':
        order_name = request.POST.get('order_name', '').strip()
        customer_name = request.POST.get('customer_name', '').strip()
        address = request.POST.get('address', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        location = request.POST.get('location', '').strip()
        delivery_date = request.POST.get('delivery_date') or None

        # Safely parse totals
        try:
            total_amount = Decimal(request.POST.get('total_amount', '0').strip() or '0')
        except (InvalidOperation, AttributeError):
            total_amount = Decimal('0')

        try:
            received_now = Decimal(request.POST.get('received_amount', '0').strip() or '0')
        except (InvalidOperation, AttributeError):
            received_now = Decimal('0')

        # Create Order (store initial received)
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

        return redirect('list_orders')

    return render(request, 'ordersapp/create_orders.html')


# -----------------------
# List Orders View
# -----------------------
def list_orders(request):
    # latest first; template can use order.received_amount and order.due_amount
    orders = Order.objects.all().order_by('-id')
    return render(request, 'ordersapp/list_orders.html', {'orders': orders})


# -----------------------
# Payment Entry View
# -----------------------
def payment_entry(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0').strip() or '0')
        except (InvalidOperation, AttributeError):
            amount = Decimal('0')

        if amount > 0:
            # Create payment record
            Payment.objects.create(order=order, amount=amount)
            # Keep Order.received_amount in sync (atomic DB-side increment)
            Order.objects.filter(id=order.id).update(
                received_amount=F('received_amount') + amount
            )

        return redirect('list_orders')

    return render(request, 'ordersapp/payment_entry.html', {'order': order})

def payment_entry_select(request):
    orders = Order.objects.all()
    return render(request, 'ordersapp/payment_entry_select.html', {'orders': orders})

# -----------------------
# Edit Order View
# -----------------------
class OrderForm(ModelForm):
    class Meta:
        model = Order
        fields = [
            'order_name', 'customer_name', 'address',
            'phone_number', 'location', 'delivery_date',
            'total_amount',  # received_amount usually not editable here
        ]

def edit_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('list_orders')
    else:
        form = OrderForm(instance=order)

    return render(request, 'ordersapp/edit_order.html', {'form': form, 'order': order})


# -----------------------
# Delete Order View
# -----------------------
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order.delete()
        return redirect('list_orders')

    return render(request, 'ordersapp/delete_order.html', {'order': order})
