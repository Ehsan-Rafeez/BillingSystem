from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import IntegrityError

from customers.models import Customer
from inventory.models import InventoryCategory, UnitOfMeasure, InventoryItem, InventoryBaseItem
from ordersapp.models import (
    Event,
    Order,
    OrderItem,
    Payment,
    MenuCategory,
    MenuItem,
    Quote,
    QuoteItem,
)


class Command(BaseCommand):
    help = "Create demo data (customers, events, inventory, menu, quotes, orders)"

    def handle(self, *args, **options):
        # Customers (avoid PK collision if auto-increment is off)
        customer = Customer.objects.filter(name="Demo Customer").first()
        if not customer:
            try:
                customer = Customer.objects.create(
                    name="Demo Customer",
                    customer_type=Customer.BUSINESS,
                    email="demo@example.com",
                    phone="03001234567",
                    address="123 Demo Street",
                    cnic="1234512345671",
                )
            except IntegrityError:
                customer = Customer.objects.filter(name="Demo Customer").first() or Customer.objects.first()
        self.stdout.write(f"Customer: {customer.name}")

        # Inventory basics: categories and units
        cat_names = ["General Supplies", "Protein", "Produce", "Staples", "Disposables", "Equipment"]
        categories = {name: InventoryCategory.objects.get_or_create(name=name)[0] for name in cat_names}
        uom_piece, _ = UnitOfMeasure.objects.get_or_create(name="Piece", defaults={"abbreviation": "pc"})
        uom_kg, _ = UnitOfMeasure.objects.get_or_create(name="Kilogram", defaults={"abbreviation": "kg"})
        uom_ltr, _ = UnitOfMeasure.objects.get_or_create(name="Liter", defaults={"abbreviation": "L"})
        uom_box, _ = UnitOfMeasure.objects.get_or_create(name="Box", defaults={"abbreviation": "box"})

        # Base catalog items (no supplier required)
        base_items = [
            {"name": "Chicken Breast", "description": "Boneless", "item_type": InventoryBaseItem.RAW, "uom": uom_kg, "price": Decimal("900.00")},
            {"name": "Basmati Rice", "description": "Premium long grain", "item_type": InventoryBaseItem.RAW, "uom": uom_kg, "price": Decimal("450.00")},
            {"name": "Cooking Oil", "description": "Canola", "item_type": InventoryBaseItem.CONSUMABLE, "uom": uom_ltr, "price": Decimal("750.00")},
            {"name": "Disposable Plates", "description": "Round white", "item_type": InventoryBaseItem.CONSUMABLE, "uom": uom_box, "price": Decimal("1200.00")},
            {"name": "Chafing Dish", "description": "Full-size stainless", "item_type": InventoryBaseItem.ASSET, "uom": uom_piece, "price": Decimal("15000.00")},
        ]
        for data in base_items:
            InventoryBaseItem.objects.get_or_create(name=data["name"], defaults=data)

        # Operational stock entries
        stock_items = [
            {
                "name": "Chafing Dish",
                "category": categories["Equipment"],
                "uom": uom_piece,
                "quantity": 20,
                "price_per_unit": Decimal("1500.00"),
                "description": "Stainless steel chafing dish",
                "total_amount": Decimal("30000.00"),
                "paid_amount": Decimal("10000.00"),
                "payment_method": "cash",
                "supplier_name": "Demo Supplier",
            },
            {
                "name": "Chicken Breast",
                "category": categories["Protein"],
                "uom": uom_kg,
                "quantity": 50,
                "price_per_unit": Decimal("900.00"),
                "description": "Boneless chicken breast for BBQ/gravies",
                "total_amount": Decimal("45000.00"),
                "paid_amount": Decimal("20000.00"),
                "payment_method": "cash",
                "supplier_name": "Meat Supplier",
            },
            {
                "name": "Basmati Rice",
                "category": categories["Staples"],
                "uom": uom_kg,
                "quantity": 100,
                "price_per_unit": Decimal("450.00"),
                "description": "Long grain basmati for biryani/pulao",
                "total_amount": Decimal("45000.00"),
                "paid_amount": Decimal("15000.00"),
                "payment_method": "cash",
                "supplier_name": "Grain Supplier",
            },
            {
                "name": "Cooking Oil",
                "category": categories["Staples"],
                "uom": uom_ltr,
                "quantity": 80,
                "price_per_unit": Decimal("750.00"),
                "description": "Canola oil for frying/cooking",
                "total_amount": Decimal("60000.00"),
                "paid_amount": Decimal("30000.00"),
                "payment_method": "bank",
                "supplier_name": "Oil Supplier",
            },
            {
                "name": "Disposable Plates",
                "category": categories["Disposables"],
                "uom": uom_box,
                "quantity": 30,
                "price_per_unit": Decimal("1200.00"),
                "description": "Round white disposable plates",
                "total_amount": Decimal("36000.00"),
                "paid_amount": Decimal("12000.00"),
                "payment_method": "cash",
                "supplier_name": "Packaging Supplier",
            },
        ]
        stock_refs = {}
        for data in stock_items:
            obj = InventoryItem.objects.filter(name=data["name"]).first()
            if not obj:
                obj = InventoryItem.objects.create(**data)
            stock_refs[data["name"]] = obj
        stock = stock_refs["Chafing Dish"]
        self.stdout.write(f"Inventory items seeded: {', '.join(stock_refs.keys())}")

        # Menu catalog
        menu_cat, _ = MenuCategory.objects.get_or_create(name="Buffet")
        menu_item = MenuItem.objects.filter(name="BBQ Platter").first()
        if not menu_item:
            menu_item = MenuItem.objects.create(
                name="BBQ Platter",
                category=menu_cat,
                description="Chicken tikka, seekh kebab, malai boti",
                price_per_portion=Decimal("850.00"),
                is_buffet=True,
            )
        self.stdout.write(f"Menu item: {menu_item.name}")

        # Event
        event = Event.objects.filter(title="Demo Corporate Lunch", customer=customer).first()
        if not event:
            event = Event.objects.create(
                title="Demo Corporate Lunch",
                event_date=date.today() + timedelta(days=7),
                customer=customer,
                event_type=Event.CORPORATE,
                location="Demo Venue",
                guest_count=80,
                dietary_notes="Halal; 10 veg",
                billing_contact_name="Mr. Demo",
                billing_contact_email="billing@example.com",
            )
        self.stdout.write(f"Event: {event.title}")

        # Quote
        quote = Quote.objects.filter(event=event, title="Quote for Demo Corporate Lunch").first()
        if not quote:
            quote = Quote.objects.create(
                event=event,
                title="Quote for Demo Corporate Lunch",
                status=Quote.SENT,
                valid_until=date.today() + timedelta(days=10),
                discount_pct=Decimal("5.00"),
            )
        QuoteItem.objects.get_or_create(
            quote=quote,
            description=menu_item.name,
            defaults={
                "menu_item": menu_item,
                "quantity": 80,
                "unit_price": menu_item.price_per_portion,
                "line_total": menu_item.price_per_portion * 80,
            },
        )
        quote.recalc_totals()
        quote.save(update_fields=["total_amount"])
        self.stdout.write(f"Quote: {quote.title} total PKR {quote.total_amount}")

        # Order with items/payment
        order = Order.objects.filter(customer_name=customer.name, event=event).first()
        if not order:
            order = Order.objects.create(
                customer_name=customer.name,
                order_date=date.today(),
                delivery_date=event.event_date,
                address="123 Demo Street",
                phone_number="03001234567",
                location=event.location,
                total_amount=Decimal("68000.00"),
                received_amount=Decimal("20000.00"),
                cnic_number="1234512345671",
                customer_type=Order.ORDER_TYPES[0][0],
                email=customer.email,
                event=event,
            )
        OrderItem.objects.get_or_create(order=order, inventory_item=stock, defaults={"quantity": 5})
        Payment.objects.get_or_create(
            order=order,
            amount=Decimal("20000.00"),
            payment_method="Cash",
            payment_date=date.today(),
        )
        self.stdout.write(f"Order: {order.id} linked to event, with payment recorded.")

        self.stdout.write(self.style.SUCCESS("Demo data seeded."))
