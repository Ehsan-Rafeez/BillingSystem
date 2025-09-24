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

        # Normalize received (optional clamp)
        if received_now < 0:
            received_now = Decimal('0')
        if total_amount >= 0 and received_now > total_amount:
            received_now = total_amount

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

    # IMPORTANT: this template will also be reused for edit mode
    return render(request, 'ordersapp/create_orders.html', {'is_edit': False})


# -----------------------
# List Orders View
# -----------------------
def list_orders(request):
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
            Payment.objects.create(order=order, amount=amount)
            Order.objects.filter(id=order.id).update(
                received_amount=F('received_amount') + amount
            )

        return redirect('list_orders')

    return render(request, 'ordersapp/payment_entry.html', {'order': order})


def payment_entry_select(request):
    orders = Order.objects.all()
    return render(request, 'ordersapp/payment_entry_select.html', {'orders': orders})


# -----------------------
# (Optional) ModelForm (not required by template)
# -----------------------
class OrderForm(ModelForm):
    class Meta:
        model = Order
        fields = [
            'order_name', 'customer_name', 'address',
            'phone_number', 'location', 'delivery_date',
            'total_amount',
        ]


# -----------------------
# Edit Order View (reuses create_orders.html)
# -----------------------
def edit_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        # Parse & update just like create, but save into existing order
        order.order_name = (request.POST.get('order_name', '') or '').strip()
        order.customer_name = (request.POST.get('customer_name', '') or '').strip()
        order.address = (request.POST.get('address', '') or '').strip()
        order.phone_number = (request.POST.get('phone_number', '') or '').strip()
        order.location = (request.POST.get('location', '') or '').strip()
        order.delivery_date = request.POST.get('delivery_date') or None

        # total_amount
        try:
            new_total = Decimal(request.POST.get('total_amount', '0').strip() or '0')
        except (InvalidOperation, AttributeError):
            new_total = order.total_amount or Decimal('0')

        # received_amount (allow editing)
        try:
            new_received = Decimal(request.POST.get('received_amount', '0').strip() or '0')
        except (InvalidOperation, AttributeError):
            new_received = order.received_amount or Decimal('0')

        # Normalize received vs total (optional clamp rules)
        if new_received < 0:
            new_received = Decimal('0')
        if new_total >= 0 and new_received > new_total:
            new_received = new_total

        order.total_amount = new_total
        order.received_amount = new_received

        order.save()
        return redirect('list_orders')

    # Render the SAME template as create, but with edit context
    return render(
        request,
        'ordersapp/create_orders.html',
        {
            'order': order,
            'is_edit': True,   # flag for template to switch to "edit mode"
        }
    )


# -----------------------
# Delete Order View
# -----------------------
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order.delete()
        return redirect('list_orders')

    return render(request, 'ordersapp/delete_order.html', {'order': order})
