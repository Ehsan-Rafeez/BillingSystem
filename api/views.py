from decimal import Decimal
import json

from django.db import transaction
from django.db.models import F, Sum
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from customers.models import Customer
from expenses.models import Expense, ExpenseCategory
from inventory.models import InventoryCategory, InventoryItem, StockMovement, UnitOfMeasure
from ordersapp.models import Event, MenuCategory, MenuItem, Order, OrderMenuItem, Payment
from suppliers.models import Supplier, SupplierPayment
from core.tenancy import assign_shop, tenant_get_object_or_404, tenant_or_global_queryset, tenant_queryset
from core.models import ApiToken


def money(value):
    return float(value or Decimal("0.00"))


def api_response(payload, status=200):
    response = JsonResponse(payload, status=status)
    response["Access-Control-Allow-Origin"] = "*"
    return response


def get_payload(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return request.POST


def parse_decimal(value, default="0.00"):
    try:
        return Decimal(str(value if value not in (None, "") else default))
    except Exception:
        return Decimal(default)


def parse_int(value, default=0):
    try:
        return int(value if value not in (None, "") else default)
    except Exception:
        return default


def parse_api_date(value, default=None):
    if not value:
        return default
    return parse_date(str(value)) or default


def parse_api_time(value):
    if not value:
        return None
    try:
        return timezone.datetime.strptime(str(value), "%H:%M").time()
    except ValueError:
        return None


def serialize_customer(customer):
    return {
        "id": customer.id,
        "customerId": customer.customer_id,
        "name": customer.name,
        "type": customer.customer_type,
        "phone": customer.phone,
        "email": customer.email,
        "address": customer.address,
        "cnic": customer.cnic,
        "taxNumber": customer.tax_number,
        "notes": customer.notes,
    }


def serialize_event(event):
    return {
        "id": event.id,
        "title": event.title,
        "customerId": event.customer_id,
        "customer": event.customer.name,
        "eventType": event.event_type,
        "eventDate": event.event_date.isoformat(),
        "eventTime": event.event_time.strftime("%H:%M") if event.event_time else "",
        "location": event.location,
        "guestCount": event.guest_count,
        "dietaryNotes": event.dietary_notes,
    }


def serialize_menu_category(category):
    return {"id": category.id, "name": category.name}


def serialize_menu_item(item):
    return {
        "id": item.id,
        "name": item.name,
        "categoryId": item.category_id,
        "category": item.category.name if item.category else "",
        "description": item.description,
        "price": money(item.price_per_portion),
        "pricingUnit": item.pricing_unit,
        "pricingUnitLabel": item.get_pricing_unit_display(),
        "isBuffet": item.is_buffet,
        "isAddon": item.is_addon,
        "isActive": item.is_active,
        "needsAttention": item.needs_attention,
    }


def serialize_order(order, detail=False):
    payload = {
        "id": order.id,
        "customer": order.customer_name,
        "phone": order.phone_number,
        "email": order.email,
        "address": order.address,
        "eventId": order.event_id,
        "event": order.event.title if order.event else "Direct Order",
        "orderDate": order.order_date.isoformat() if order.order_date else "",
        "date": order.delivery_date.isoformat() if order.delivery_date else "",
        "deliveryTime": order.delivery_time.strftime("%H:%M") if order.delivery_time else "",
        "cateringDate": order.catering_date.isoformat() if order.catering_date else "",
        "cateringTime": order.catering_time.strftime("%H:%M") if order.catering_time else "",
        "location": order.location or "",
        "grossTotal": money(order.gross_amount),
        "netTotal": money(order.total_amount),
        "discount": money(order.discount_amount),
        "received": money(order.received_amount),
        "due": money(order.due_amount),
        "status": "Delivered" if order.status == Order.STATUS_DELIVERED else "Pending",
    }
    if detail:
        payload["items"] = [
            {
                "id": line.id,
                "menuItemId": line.menu_item_id,
                "name": line.menu_item.name,
                "pricingUnit": line.menu_item.get_pricing_unit_display(),
                "quantity": line.quantity,
                "unitPrice": money(line.menu_item.price_per_portion),
                "note": line.note,
            }
            for line in order.menu_items.select_related("menu_item")
        ]
        payload["payments"] = [
            {
                "id": payment.id,
                "amount": money(payment.amount),
                "date": payment.payment_date.isoformat(),
                "method": payment.payment_method,
            }
            for payment in order.payments.order_by("-payment_date", "-id")
        ]
    return payload


@require_GET
def health(request):
    return api_response({"status": "ok"})


@csrf_exempt
@require_POST
def login(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = request.POST

    username = payload.get("username")
    password = payload.get("password")
    user = authenticate(request, username=username, password=password)
    if not user:
        return api_response({"ok": False, "error": "Invalid username or password."}, status=400)
    if not user.is_superuser and not user.owned_shops.filter(is_active=True).exists():
        return api_response({"ok": False, "error": "No active shop is assigned to this user."}, status=403)

    token, _created = ApiToken.objects.get_or_create(user=user)
    shop = user.owned_shops.filter(is_active=True).order_by("id").first()
    return api_response(
        {
            "ok": True,
            "token": token.token,
            "user": {
                "username": user.username,
                "isSuperuser": user.is_superuser,
            },
            "shop": {
                "id": shop.id,
                "name": shop.name,
                "slug": shop.slug,
            }
            if shop
            else None,
        }
    )


@require_GET
def dashboard(request):
    orders_qs = tenant_queryset(request, Order.objects.all())
    inventory_qs = tenant_queryset(request, InventoryItem.objects.all())
    suppliers_qs = tenant_queryset(request, Supplier.objects.all())
    order_totals = orders_qs.aggregate(
        net=Sum("total_amount"),
        received=Sum("received_amount"),
        discount=Sum("discount_amount"),
    )
    supplier_totals = suppliers_qs.aggregate(
        purchases=Sum("total_purchases"),
        paid=Sum("total_paid"),
    )
    supplier_balance = (supplier_totals["purchases"] or Decimal("0.00")) - (
        supplier_totals["paid"] or Decimal("0.00")
    )

    return api_response(
        {
            "net": money(order_totals["net"]),
            "received": money(order_totals["received"]),
            "discount": money(order_totals["discount"]),
            "due": money((order_totals["net"] or Decimal("0.00")) - (order_totals["received"] or Decimal("0.00"))),
            "ordersCount": orders_qs.count(),
            "pending": orders_qs.filter(status=Order.STATUS_PENDING).count(),
            "delivered": orders_qs.filter(status=Order.STATUS_DELIVERED).count(),
            "lowStock": inventory_qs.filter(quantity__lte=5).count(),
            "supplierBalance": money(supplier_balance),
        }
    )


@require_GET
def orders(request):
    rows = []
    qs = tenant_queryset(request, Order.objects.select_related("event")).order_by("-id")[:50]
    for order in qs:
        rows.append(serialize_order(order))
    return api_response({"orders": rows})


@require_GET
def order_meta(request):
    return api_response(
        {
            "customers": [serialize_customer(c) for c in tenant_queryset(request, Customer.objects.all()).order_by("name")],
            "events": [serialize_event(e) for e in tenant_queryset(request, Event.objects.select_related("customer")).order_by("-event_date")],
            "menuItems": [serialize_menu_item(i) for i in tenant_queryset(request, MenuItem.objects.select_related("category").filter(is_active=True)).order_by("name")],
            "pricingUnits": [{"value": v, "label": label} for v, label in MenuItem.PRICING_UNIT_CHOICES],
        }
    )


def upsert_customer_from_payload(request, payload):
    name = (payload.get("customerName") or payload.get("customer") or "").strip()
    phone = (payload.get("phone") or "").strip()
    email = (payload.get("email") or "").strip()
    address = (payload.get("address") or "").strip()
    cnic = (payload.get("cnic") or "").strip()
    if not name:
        return None
    qs = tenant_queryset(request, Customer.objects.all())
    customer = qs.filter(phone=phone).first() if phone else None
    if customer is None and email:
        customer = qs.filter(email__iexact=email).first()
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


def apply_order_payload(request, order, payload):
    gross = parse_decimal(payload.get("grossAmount") or payload.get("gross_amount") or payload.get("totalAmount") or "0")
    discount = parse_decimal(payload.get("discountAmount") or payload.get("discount") or "0")
    if discount < 0:
        discount = Decimal("0.00")
    if discount > gross:
        discount = gross
    received = parse_decimal(payload.get("receivedAmount") or payload.get("received") or "0")
    total = gross - discount
    if received < 0:
        received = Decimal("0.00")
    if received > total:
        received = total

    order.order_date = parse_api_date(payload.get("orderDate"), timezone.localdate())
    order.customer_name = (payload.get("customerName") or payload.get("customer") or "").strip()
    order.phone_number = (payload.get("phone") or "").strip()
    order.email = (payload.get("email") or "").strip()
    order.address = (payload.get("address") or "").strip()
    order.location = (payload.get("location") or "").strip()
    order.cnic_number = (payload.get("cnic") or "0000000000000").strip() or "0000000000000"
    order.customer_type = payload.get("customerType") or "regular"
    order.delivery_date = parse_api_date(payload.get("deliveryDate") or payload.get("date"), timezone.localdate())
    order.delivery_time = parse_api_time(payload.get("deliveryTime"))
    order.catering_date = parse_api_date(payload.get("cateringDate"), order.delivery_date)
    order.catering_time = parse_api_time(payload.get("cateringTime"))
    order.event_id = payload.get("eventId") or None
    order.discount_amount = discount
    order.total_amount = total
    order.received_amount = received
    assign_shop(request, order)
    return order


@csrf_exempt
@require_POST
def order_create(request):
    payload = get_payload(request)
    items = payload.get("items") or []
    if not items:
        return api_response({"ok": False, "error": "Add at least one menu item."}, status=400)
    try:
        with transaction.atomic():
            order = apply_order_payload(request, Order(), payload)
            if not order.customer_name:
                return api_response({"ok": False, "error": "Customer name is required."}, status=400)
            order.save()
            upsert_customer_from_payload(request, payload)
            for row in items:
                menu_item = tenant_get_object_or_404(request, MenuItem.objects.all(), id=row.get("menuItemId") or row.get("id"))
                quantity = parse_int(row.get("quantity"), 1)
                if quantity <= 0:
                    continue
                OrderMenuItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=quantity,
                    note=(row.get("note") or "").strip(),
                )
            if order.received_amount > 0:
                Payment.objects.create(order=order, amount=order.received_amount)
    except Exception as exc:
        return api_response({"ok": False, "error": str(exc)}, status=400)
    return api_response({"ok": True, "order": serialize_order(order, detail=True)}, status=201)


@require_GET
def order_detail(request, order_id):
    order = tenant_get_object_or_404(
        request,
        Order.objects.select_related("event").prefetch_related("menu_items__menu_item", "payments"),
        id=order_id,
    )
    return api_response({"order": serialize_order(order, detail=True)})


@csrf_exempt
@require_POST
def order_update(request, order_id):
    order = tenant_get_object_or_404(request, Order.objects.all(), id=order_id)
    payload = get_payload(request)
    items = payload.get("items")
    try:
        with transaction.atomic():
            order = apply_order_payload(request, order, payload)
            order.save()
            upsert_customer_from_payload(request, payload)
            if items is not None:
                order.menu_items.all().delete()
                for row in items:
                    menu_item = tenant_get_object_or_404(request, MenuItem.objects.all(), id=row.get("menuItemId") or row.get("id"))
                    quantity = parse_int(row.get("quantity"), 1)
                    if quantity > 0:
                        OrderMenuItem.objects.create(order=order, menu_item=menu_item, quantity=quantity, note=(row.get("note") or "").strip())
    except Exception as exc:
        return api_response({"ok": False, "error": str(exc)}, status=400)
    return api_response({"ok": True, "order": serialize_order(order, detail=True)})


@csrf_exempt
@require_POST
def order_payment_create(request, order_id):
    order = tenant_get_object_or_404(request, Order.objects.all(), id=order_id)
    payload = get_payload(request)
    amount = parse_decimal(payload.get("amount"), "0")
    if amount <= 0:
        return api_response({"ok": False, "error": "Payment amount must be greater than zero."}, status=400)
    Payment.objects.create(
        order=order,
        amount=amount,
        payment_method=payload.get("paymentMethod") or "Cash",
        payment_date=parse_api_date(payload.get("paymentDate"), timezone.localdate()),
    )
    Order.objects.filter(id=order.id).update(received_amount=F("received_amount") + amount)
    order.refresh_from_db()
    return api_response({"ok": True, "order": serialize_order(order)})


@csrf_exempt
@require_POST
def order_deliver(request, order_id):
    order = tenant_get_object_or_404(request, Order.objects.all(), id=order_id)
    order.status = Order.STATUS_DELIVERED
    order.delivered_at = timezone.now()
    order.save(update_fields=["status", "delivered_at"])
    return api_response({"ok": True, "order": serialize_order(order)})


@csrf_exempt
@require_POST
def order_delete(request, order_id):
    order = tenant_get_object_or_404(request, Order.objects.all(), id=order_id)
    order.delete()
    return api_response({"ok": True})


@require_GET
def customers(request):
    qs = tenant_queryset(request, Customer.objects.all()).order_by("name")
    return api_response({"customers": [serialize_customer(c) for c in qs]})


@csrf_exempt
@require_POST
def customer_create(request):
    payload = get_payload(request)
    customer = Customer(
        name=(payload.get("name") or "").strip(),
        customer_type=payload.get("type") or Customer.INDIVIDUAL,
        phone=(payload.get("phone") or "").strip(),
        email=(payload.get("email") or "").strip(),
        address=(payload.get("address") or "").strip(),
        cnic=(payload.get("cnic") or "").strip(),
        tax_number=(payload.get("taxNumber") or "").strip(),
        notes=(payload.get("notes") or "").strip(),
    )
    if not customer.name:
        return api_response({"ok": False, "error": "Customer name is required."}, status=400)
    assign_shop(request, customer)
    customer.save()
    return api_response({"ok": True, "customer": serialize_customer(customer)}, status=201)


@require_GET
def events(request):
    qs = tenant_queryset(request, Event.objects.select_related("customer")).order_by("-event_date")
    return api_response({"events": [serialize_event(e) for e in qs]})


@csrf_exempt
@require_POST
def event_create(request):
    payload = get_payload(request)
    customer_id = payload.get("customerId")
    customer = tenant_get_object_or_404(request, Customer.objects.all(), id=customer_id)
    event = Event(
        customer=customer,
        title=(payload.get("title") or "").strip(),
        event_type=payload.get("eventType") or Event.OTHER,
        event_date=parse_api_date(payload.get("eventDate"), timezone.localdate()),
        event_time=parse_api_time(payload.get("eventTime")),
        location=(payload.get("location") or "").strip(),
        guest_count=parse_int(payload.get("guestCount"), 0),
        dietary_notes=(payload.get("dietaryNotes") or "").strip(),
        billing_contact_name=(payload.get("billingContactName") or "").strip(),
        billing_contact_phone=(payload.get("billingContactPhone") or "").strip(),
        billing_contact_email=(payload.get("billingContactEmail") or "").strip(),
        additional_notes=(payload.get("notes") or "").strip(),
    )
    if not event.title:
        return api_response({"ok": False, "error": "Event title is required."}, status=400)
    if not event.location:
        return api_response({"ok": False, "error": "Event location is required."}, status=400)
    assign_shop(request, event)
    event.save()
    return api_response({"ok": True, "event": serialize_event(event)}, status=201)


@require_GET
def menu_categories(request):
    qs = tenant_queryset(request, MenuCategory.objects.all()).order_by("name")
    return api_response({"categories": [serialize_menu_category(c) for c in qs]})


@csrf_exempt
@require_POST
def menu_category_create(request):
    payload = get_payload(request)
    name = (payload.get("name") or "").strip()
    if not name:
        return api_response({"ok": False, "error": "Category name is required."}, status=400)
    category = MenuCategory(name=name)
    assign_shop(request, category)
    try:
        category.save()
    except Exception as exc:
        return api_response({"ok": False, "error": str(exc)}, status=400)
    return api_response({"ok": True, "category": serialize_menu_category(category)}, status=201)


@require_GET
def menu_items(request):
    qs = tenant_queryset(request, MenuItem.objects.select_related("category")).order_by("name")
    return api_response(
        {
            "items": [serialize_menu_item(i) for i in qs],
            "pricingUnits": [{"value": v, "label": label} for v, label in MenuItem.PRICING_UNIT_CHOICES],
        }
    )


def apply_menu_item_payload(request, item, payload):
    item.name = (payload.get("name") or "").strip()
    item.category_id = payload.get("categoryId") or payload.get("category") or None
    item.description = (payload.get("description") or payload.get("note") or "").strip()
    item.price_per_portion = parse_decimal(payload.get("price") or payload.get("pricePerPortion") or payload.get("price_per_portion"), "0")
    item.pricing_unit = payload.get("pricingUnit") or MenuItem.UNIT_HEAD
    item.is_buffet = bool(payload.get("isBuffet", False))
    item.is_addon = bool(payload.get("isAddon", False))
    item.is_active = bool(payload.get("isActive", True))
    item.needs_attention = bool(payload.get("needsAttention", False))
    assign_shop(request, item)
    return item


@csrf_exempt
@require_POST
def menu_item_create(request):
    payload = get_payload(request)
    item = apply_menu_item_payload(request, MenuItem(), payload)
    if not item.name:
        return api_response({"ok": False, "error": "Menu item name is required."}, status=400)
    try:
        item.save()
    except Exception as exc:
        return api_response({"ok": False, "error": str(exc)}, status=400)
    return api_response({"ok": True, "item": serialize_menu_item(item)}, status=201)


@csrf_exempt
@require_POST
def menu_item_update(request, item_id):
    item = tenant_get_object_or_404(request, MenuItem.objects.all(), id=item_id)
    item = apply_menu_item_payload(request, item, get_payload(request))
    if not item.name:
        return api_response({"ok": False, "error": "Menu item name is required."}, status=400)
    item.save()
    return api_response({"ok": True, "item": serialize_menu_item(item)})


@require_GET
def inventory(request):
    rows = []
    qs = tenant_queryset(request, InventoryItem.objects.select_related("uom", "category")).order_by("name")[:100]
    for item in qs:
        if item.quantity <= item.min_quantity:
            status = "Critical"
        elif item.quantity <= item.min_quantity + 5:
            status = "Low"
        else:
            status = "Healthy"

        rows.append(
            {
                "id": item.id,
                "name": item.name,
                "quantity": item.quantity,
                "unit": item.uom.abbreviation,
                "category": item.category.name,
                "status": status,
                "remainingPayment": money(item.remaining),
            }
        )
    return api_response({"inventory": rows})


@require_GET
def inventory_meta(request):
    categories = tenant_or_global_queryset(request, InventoryCategory.objects.all()).order_by("name")
    uoms = tenant_or_global_queryset(request, UnitOfMeasure.objects.all()).order_by("name")
    return api_response(
        {
            "categories": [{"id": c.id, "name": c.name} for c in categories],
            "units": [{"id": u.id, "name": u.name, "abbreviation": u.abbreviation} for u in uoms],
        }
    )


@csrf_exempt
@require_POST
def inventory_create(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = request.POST

    try:
        name = (payload.get("name") or "").strip()
        category_id = payload.get("categoryId") or payload.get("category")
        uom_id = payload.get("uomId") or payload.get("uom")
        quantity = int(payload.get("quantity") or 1)
        price_per_unit = Decimal(str(payload.get("pricePerUnit") or payload.get("price_per_unit") or "0"))
        supplier_name = (payload.get("supplierName") or payload.get("supplier_name") or "Manual entry").strip()
        description = (payload.get("description") or "").strip()

        if not name:
            return api_response({"ok": False, "error": "Item name is required."}, status=400)
        if quantity <= 0:
            return api_response({"ok": False, "error": "Quantity must be greater than zero."}, status=400)
        if price_per_unit < 0:
            return api_response({"ok": False, "error": "Price cannot be negative."}, status=400)

        category = tenant_get_object_or_404(request, tenant_or_global_queryset(request, InventoryCategory.objects.all()), id=category_id)
        uom = tenant_get_object_or_404(request, tenant_or_global_queryset(request, UnitOfMeasure.objects.all()), id=uom_id)
        item = InventoryItem.objects.create(
            name=name,
            category=category,
            uom=uom,
            quantity=quantity,
            price_per_unit=price_per_unit,
            description=description,
            supplier_name=supplier_name,
            total_amount=price_per_unit * quantity,
            paid_amount=Decimal("0.00"),
            payment_method="cash",
        )
        assign_shop(request, item)
        item.save(update_fields=["shop"])
        StockMovement.objects.create(
            inventory_item=item,
            movement_type=StockMovement.IN,
            quantity=quantity,
            note="Initial inventory entry from mobile",
        )
    except Exception as exc:
        return api_response({"ok": False, "error": str(exc)}, status=400)

    return api_response(
        {
            "ok": True,
            "item": {
                "id": item.id,
                "name": item.name,
                "quantity": item.quantity,
                "unit": item.uom.abbreviation,
                "category": item.category.name,
                "remainingPayment": money(item.remaining),
            },
        },
        status=201,
    )


@csrf_exempt
@require_POST
def inventory_update(request, item_id):
    item = tenant_get_object_or_404(request, InventoryItem.objects.all(), id=item_id)
    payload = get_payload(request)
    try:
        item.name = (payload.get("name") or item.name).strip()
        if payload.get("categoryId") or payload.get("category"):
            item.category = tenant_get_object_or_404(request, tenant_or_global_queryset(request, InventoryCategory.objects.all()), id=payload.get("categoryId") or payload.get("category"))
        if payload.get("uomId") or payload.get("uom"):
            item.uom = tenant_get_object_or_404(request, tenant_or_global_queryset(request, UnitOfMeasure.objects.all()), id=payload.get("uomId") or payload.get("uom"))
        item.quantity = parse_int(payload.get("quantity"), item.quantity)
        item.price_per_unit = parse_decimal(payload.get("pricePerUnit") or payload.get("price_per_unit"), str(item.price_per_unit))
        item.description = (payload.get("description") or item.description or "").strip()
        item.supplier_name = (payload.get("supplierName") or payload.get("supplier_name") or item.supplier_name or "Manual entry").strip()
        item.total_amount = item.price_per_unit * item.quantity
        assign_shop(request, item)
        item.save()
    except Exception as exc:
        return api_response({"ok": False, "error": str(exc)}, status=400)
    return api_response({"ok": True, "item": {"id": item.id, "name": item.name, "quantity": item.quantity}})


@csrf_exempt
@require_POST
def inventory_restock(request, item_id):
    item = tenant_get_object_or_404(request, InventoryItem.objects.all(), id=item_id)
    payload = get_payload(request)
    quantity = parse_decimal(payload.get("quantity"), "0")
    if quantity <= 0:
        return api_response({"ok": False, "error": "Quantity must be greater than zero."}, status=400)
    InventoryItem.objects.filter(id=item.id).update(quantity=F("quantity") + quantity)
    StockMovement.objects.create(
        inventory_item=item,
        movement_type=StockMovement.IN,
        quantity=quantity,
        note=(payload.get("note") or "Mobile restock").strip(),
    )
    item.refresh_from_db()
    return api_response({"ok": True, "item": {"id": item.id, "name": item.name, "quantity": item.quantity}})


@csrf_exempt
@require_POST
def inventory_delete(request, item_id):
    item = tenant_get_object_or_404(request, InventoryItem.objects.all(), id=item_id)
    item.delete()
    return api_response({"ok": True})


@require_GET
def suppliers(request):
    rows = []
    qs = tenant_queryset(request, Supplier.objects.prefetch_related("payments").filter(is_active=True)).order_by("name")[:100]
    for supplier in qs:
        last_payment = supplier.payments.first()
        rows.append(
            {
                "id": supplier.id,
                "name": supplier.name,
                "balance": money(supplier.balance_due),
                "phone": supplier.phone,
                "lastPayment": last_payment.payment_date.isoformat() if last_payment else "No payments",
            }
        )
    return api_response({"suppliers": rows})


@csrf_exempt
@require_POST
def supplier_create(request):
    payload = get_payload(request)
    supplier = Supplier(
        name=(payload.get("name") or "").strip(),
        supplier_type=payload.get("type") or Supplier.BUSINESS,
        email=(payload.get("email") or "").strip(),
        phone=(payload.get("phone") or "").strip(),
        contact_person=(payload.get("contactPerson") or "").strip(),
        tax_number=(payload.get("taxNumber") or "").strip(),
        notes=(payload.get("notes") or "").strip(),
        address=(payload.get("address") or "").strip(),
    )
    if not supplier.name:
        return api_response({"ok": False, "error": "Supplier name is required."}, status=400)
    assign_shop(request, supplier)
    supplier.save()
    return api_response({"ok": True, "supplier": {"id": supplier.id, "name": supplier.name}}, status=201)


@csrf_exempt
@require_POST
def supplier_payment_create(request, supplier_id):
    supplier = tenant_get_object_or_404(request, Supplier.objects.all(), id=supplier_id)
    payload = get_payload(request)
    amount = parse_decimal(payload.get("amount"), "0")
    if amount <= 0:
        return api_response({"ok": False, "error": "Payment amount must be greater than zero."}, status=400)
    payment = SupplierPayment.objects.create(
        supplier=supplier,
        amount=amount,
        payment_date=parse_api_date(payload.get("paymentDate"), timezone.localdate()),
        payment_method=payload.get("paymentMethod") or "Cash",
        reference_number=(payload.get("reference") or "").strip(),
        notes=(payload.get("notes") or "").strip(),
    )
    return api_response({"ok": True, "payment": {"id": payment.id, "amount": money(payment.amount)}})


def serialize_expense(expense):
    return {
        "id": expense.id,
        "date": expense.date.isoformat(),
        "categoryId": expense.category_id,
        "category": expense.category.name if expense.category else "Uncategorized",
        "description": expense.description,
        "amount": money(expense.amount),
        "supplierName": expense.supplier_name,
        "reference": expense.reference,
        "paymentMethod": expense.payment_method,
    }


@require_GET
def expenses(request):
    qs = tenant_queryset(request, Expense.objects.select_related("category")).order_by("-date", "-id")[:100]
    return api_response({"expenses": [serialize_expense(e) for e in qs]})


@require_GET
def expense_meta(request):
    categories = tenant_or_global_queryset(request, ExpenseCategory.objects.all()).order_by("name")
    return api_response({"categories": [{"id": c.id, "name": c.name} for c in categories]})


@csrf_exempt
@require_POST
def expense_create(request):
    payload = get_payload(request)
    category = None
    if payload.get("categoryId") or payload.get("category"):
        category = tenant_get_object_or_404(request, tenant_or_global_queryset(request, ExpenseCategory.objects.all()), id=payload.get("categoryId") or payload.get("category"))
    expense = Expense(
        date=parse_api_date(payload.get("date"), timezone.localdate()),
        category=category,
        description=(payload.get("description") or "").strip(),
        amount=parse_decimal(payload.get("amount"), "0"),
        supplier_name=(payload.get("supplierName") or "").strip(),
        reference=(payload.get("reference") or "").strip(),
        payment_method=payload.get("paymentMethod") or Expense.CASH,
    )
    if expense.amount <= 0:
        return api_response({"ok": False, "error": "Expense amount must be greater than zero."}, status=400)
    assign_shop(request, expense)
    expense.save()
    return api_response({"ok": True, "expense": serialize_expense(expense)}, status=201)


def serialize_shop_settings(shop):
    return {
        "id": shop.id,
        "name": shop.name,
        "invoiceShopName": shop.invoice_shop_name,
        "phone": shop.phone,
        "address": shop.address,
        "bankName": shop.bank_name,
        "bankAccountTitle": shop.bank_account_title,
        "bankAccountNumber": shop.bank_account_number,
        "bankIban": shop.bank_iban,
        "bankBranch": shop.bank_branch,
        "bankBranchCode": shop.bank_branch_code,
        "bankSwiftCode": shop.bank_swift_code,
        "bankPaymentInstructions": shop.bank_payment_instructions,
        "showInvoiceShopName": shop.show_invoice_shop_name,
        "showInvoiceLogo": shop.show_invoice_logo,
        "showInvoiceBankDetails": shop.show_invoice_bank_details,
        "logoUrl": shop.invoice_logo.url if shop.invoice_logo else "",
    }


@require_GET
def shop_settings(request):
    shop = getattr(request, "shop", None)
    if not shop:
        return api_response({"ok": False, "error": "No active shop is assigned."}, status=403)
    return api_response({"settings": serialize_shop_settings(shop)})


@csrf_exempt
@require_POST
def shop_settings_update(request):
    shop = getattr(request, "shop", None)
    if not shop:
        return api_response({"ok": False, "error": "No active shop is assigned."}, status=403)
    payload = get_payload(request)
    shop.invoice_shop_name = (payload.get("invoiceShopName") or "").strip()
    shop.phone = (payload.get("phone") or shop.phone or "").strip()
    shop.address = (payload.get("address") or shop.address or "").strip()
    shop.bank_name = (payload.get("bankName") or "").strip()
    shop.bank_account_title = (payload.get("bankAccountTitle") or "").strip()
    shop.bank_account_number = (payload.get("bankAccountNumber") or "").strip()
    shop.bank_iban = (payload.get("bankIban") or "").strip()
    shop.bank_branch = (payload.get("bankBranch") or "").strip()
    shop.bank_branch_code = (payload.get("bankBranchCode") or "").strip()
    shop.bank_swift_code = (payload.get("bankSwiftCode") or "").strip()
    shop.bank_payment_instructions = (payload.get("bankPaymentInstructions") or "").strip()
    shop.show_invoice_shop_name = bool(payload.get("showInvoiceShopName", True))
    shop.show_invoice_logo = bool(payload.get("showInvoiceLogo", True))
    shop.show_invoice_bank_details = bool(payload.get("showInvoiceBankDetails", True))
    shop.save()
    return api_response({"ok": True, "settings": serialize_shop_settings(shop)})
