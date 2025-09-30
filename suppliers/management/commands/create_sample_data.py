from django.core.management.base import BaseCommand
from suppliers.models import Supplier, SupplierPayment, PurchaseOrder, PurchaseOrderItem
from inventory.models import InventoryItem, UnitOfMeasure
from decimal import Decimal
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Create sample supplier data for testing'

    def handle(self, *args, **options):
        # Create Unit of Measure if it doesn't exist
        uom, created = UnitOfMeasure.objects.get_or_create(
            name='Piece',
            defaults={'abbreviation': 'pcs'}
        )
        
        # Create sample suppliers
        suppliers_data = [
            {
                'name': 'ABC Food Supplies',
                'supplier_type': 'BUS',
                'email': 'contact@abcfoods.com',
                'phone': '+1-555-0101',
                'contact_person': 'John Smith',
                'tax_number': 'TAX123456',
                'address': '123 Food Street, City, State 12345',
                'notes': 'Primary food supplier for raw materials'
            },
            {
                'name': 'XYZ Equipment Co.',
                'supplier_type': 'BUS',
                'email': 'sales@xyzequipment.com',
                'phone': '+1-555-0102',
                'contact_person': 'Jane Doe',
                'tax_number': 'TAX789012',
                'address': '456 Equipment Ave, City, State 12345',
                'notes': 'Equipment and asset supplier'
            },
            {
                'name': 'Local Paper Products',
                'supplier_type': 'BUS',
                'email': 'orders@localpaper.com',
                'phone': '+1-555-0103',
                'contact_person': 'Bob Johnson',
                'tax_number': 'TAX345678',
                'address': '789 Paper Road, City, State 12345',
                'notes': 'Consumable supplies like napkins, boxes'
            }
        ]
        
        suppliers = []
        for supplier_data in suppliers_data:
            if not Supplier.objects.filter(name=supplier_data['name']).exists():
                supplier = Supplier.objects.create(**supplier_data)
                suppliers.append(supplier)
                self.stdout.write(f'Created supplier: {supplier.name}')
            else:
                supplier = Supplier.objects.get(name=supplier_data['name'])
                suppliers.append(supplier)
                self.stdout.write(f'Found existing supplier: {supplier.name}')
        
        # Create sample inventory items with suppliers
        inventory_items_data = [
            {
                'name': 'Chicken Breast',
                'description': 'Fresh chicken breast for cooking',
                'item_type': 'RAW',
                'uom': uom,
                'price': Decimal('8.50'),
                'cost_per_uom': Decimal('6.00'),
                'supplier': suppliers[0]
            },
            {
                'name': 'Cooking Oil',
                'description': 'Vegetable cooking oil',
                'item_type': 'RAW',
                'uom': uom,
                'price': Decimal('12.00'),
                'cost_per_uom': Decimal('8.50'),
                'supplier': suppliers[0]
            },
            {
                'name': 'Catering Chairs',
                'description': 'Folding chairs for events',
                'item_type': 'ASSET',
                'uom': uom,
                'price': Decimal('25.00'),
                'cost_per_uom': Decimal('15.00'),
                'supplier': suppliers[1]
            },
            {
                'name': 'Paper Napkins',
                'description': 'Disposable paper napkins',
                'item_type': 'CONS',
                'uom': uom,
                'price': Decimal('5.00'),
                'cost_per_uom': Decimal('2.50'),
                'supplier': suppliers[2]
            }
        ]
        
        inventory_items = []
        for item_data in inventory_items_data:
            if not InventoryItem.objects.filter(name=item_data['name']).exists():
                item = InventoryItem.objects.create(**item_data)
                inventory_items.append(item)
                self.stdout.write(f'Created inventory item: {item.name}')
            else:
                item = InventoryItem.objects.get(name=item_data['name'])
                inventory_items.append(item)
                self.stdout.write(f'Found existing inventory item: {item.name}')
        
        # Create sample purchase orders
        purchase_orders_data = [
            {
                'supplier': suppliers[0],
                'order_date': date.today() - timedelta(days=30),
                'expected_delivery_date': date.today() - timedelta(days=25),
                'status': 'COMPLETED',
                'notes': 'Monthly food supplies order'
            },
            {
                'supplier': suppliers[1],
                'order_date': date.today() - timedelta(days=15),
                'expected_delivery_date': date.today() - timedelta(days=10),
                'status': 'PENDING',
                'notes': 'New equipment for upcoming events'
            },
            {
                'supplier': suppliers[2],
                'order_date': date.today() - timedelta(days=7),
                'expected_delivery_date': date.today() + timedelta(days=3),
                'status': 'PARTIAL',
                'notes': 'Consumable supplies restock'
            }
        ]
        
        purchase_orders = []
        for i, po_data in enumerate(purchase_orders_data):
            if not PurchaseOrder.objects.filter(supplier=po_data['supplier'], order_date=po_data['order_date']).exists():
                po = PurchaseOrder.objects.create(**po_data)
                purchase_orders.append(po)
                self.stdout.write(f'Created purchase order: {po.order_number}')
            else:
                po = PurchaseOrder.objects.get(supplier=po_data['supplier'], order_date=po_data['order_date'])
                purchase_orders.append(po)
                self.stdout.write(f'Found existing purchase order: {po.order_number}')
        
        # Create sample purchase order items
        po_items_data = [
            # PO 1 - Food supplies
            {
                'purchase_order': purchase_orders[0],
                'inventory_item': inventory_items[0],
                'quantity': Decimal('50.0000'),
                'unit_price': Decimal('6.0000')
            },
            {
                'purchase_order': purchase_orders[0],
                'inventory_item': inventory_items[1],
                'quantity': Decimal('20.0000'),
                'unit_price': Decimal('8.5000')
            },
            # PO 2 - Equipment
            {
                'purchase_order': purchase_orders[1],
                'inventory_item': inventory_items[2],
                'quantity': Decimal('25.0000'),
                'unit_price': Decimal('15.0000')
            },
            # PO 3 - Consumables
            {
                'purchase_order': purchase_orders[2],
                'inventory_item': inventory_items[3],
                'quantity': Decimal('100.0000'),
                'unit_price': Decimal('2.5000')
            }
        ]
        
        for item_data in po_items_data:
            if not PurchaseOrderItem.objects.filter(purchase_order=item_data['purchase_order'], inventory_item=item_data['inventory_item']).exists():
                po_item = PurchaseOrderItem.objects.create(**item_data)
                self.stdout.write(f'Created PO item: {po_item.inventory_item.name}')
            else:
                self.stdout.write(f'Found existing PO item: {item_data["inventory_item"].name}')
        
        # Create sample payments
        payments_data = [
            {
                'supplier': suppliers[0],
                'amount': Decimal('500.00'),
                'payment_date': date.today() - timedelta(days=20),
                'payment_method': 'Bank',
                'reference_number': 'CHK001234',
                'notes': 'Payment for food supplies order'
            },
            {
                'supplier': suppliers[0],
                'amount': Decimal('200.00'),
                'payment_date': date.today() - timedelta(days=5),
                'payment_method': 'Cash',
                'reference_number': '',
                'notes': 'Partial payment for outstanding balance'
            },
            {
                'supplier': suppliers[2],
                'amount': Decimal('150.00'),
                'payment_date': date.today() - timedelta(days=2),
                'payment_method': 'Card',
                'reference_number': 'TXN567890',
                'notes': 'Payment for paper products'
            }
        ]
        
        for payment_data in payments_data:
            if not SupplierPayment.objects.filter(supplier=payment_data['supplier'], amount=payment_data['amount'], payment_date=payment_data['payment_date']).exists():
                payment = SupplierPayment.objects.create(**payment_data)
                self.stdout.write(f'Created payment: ${payment.amount} for {payment.supplier.name}')
            else:
                self.stdout.write(f'Found existing payment: ${payment_data["amount"]} for {payment_data["supplier"].name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample supplier data!')
        )
