from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from carts.models import Cart, CartItem
from catalog.models import Category, Product
from commerce.models import Notification
from orders.models import Order

from .models import AIInsightReport, InventoryAlert, InventoryBatch, InventoryMovement
from .services import scan_inventory


class InventoryApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="inventory-manager",
            email="inventory@example.com",
            password="password123",
            is_staff=True,
        )
        self.customer = user_model.objects.create_user(
            username="inventory-customer",
            email="customer@example.com",
            password="password123",
        )
        category = Category.objects.create(name="أغذية", slug="inventory-food")
        self.product = Product.objects.create(
            category=category,
            name="قهوة مختصة",
            slug="inventory-coffee",
            sku="INV-COFFEE-1",
            price_cents=5000,
            stock=2,
            low_stock_threshold=3,
            reorder_quantity=12,
        )

    def test_dashboard_is_staff_only(self):
        self.client.force_authenticate(self.customer)
        response = self.client.get(reverse("inventory-dashboard"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.staff)
        response = self.client.get(reverse("inventory-dashboard"), {"days": 30})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["overview"]["low_stock_items"], 1)
        self.assertEqual(response.data["stock"][0]["reorder_quantity"], 12)

    def test_restock_creates_batch_movement_and_expiry_alert(self):
        self.client.force_authenticate(self.staff)
        expires_at = timezone.localdate() + timedelta(days=7)
        response = self.client.post(
            reverse("inventory-adjust"),
            {
                "product": self.product.id,
                "quantity_delta": 10,
                "kind": InventoryMovement.Kind.RESTOCK,
                "reason": "توريد تجريبي",
                "lot_number": "LOT-2026-01",
                "expires_at": expires_at.isoformat(),
                "unit_cost_cents": 2600,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 12)
        self.assertTrue(
            InventoryBatch.objects.filter(
                product=self.product,
                lot_number="LOT-2026-01",
                quantity=10,
                expires_at=expires_at,
            ).exists()
        )
        self.assertTrue(
            InventoryMovement.objects.filter(
                product=self.product,
                kind=InventoryMovement.Kind.RESTOCK,
                quantity_delta=10,
            ).exists()
        )
        self.assertTrue(
            InventoryAlert.objects.filter(
                product=self.product,
                alert_type=InventoryAlert.Type.EXPIRING,
                is_active=True,
            ).exists()
        )

    def test_scan_creates_one_staff_notification_for_new_alert(self):
        result = scan_inventory(send_notifications=True)
        self.assertEqual(result["new_notifications"], 1)
        self.assertEqual(Notification.objects.filter(user=self.staff, kind="inventory").count(), 1)

        result = scan_inventory(send_notifications=True)
        self.assertEqual(result["new_notifications"], 0)
        self.assertEqual(Notification.objects.filter(user=self.staff, kind="inventory").count(), 1)

    def test_scan_detects_slow_moving_stock(self):
        slow_product = Product.objects.create(
            category=self.product.category,
            name="صنف راكد",
            slug="slow-inventory-item",
            sku="INV-SLOW-1",
            price_cents=2500,
            stock=20,
            low_stock_threshold=3,
        )
        scan_inventory(send_notifications=False)
        self.assertTrue(
            InventoryAlert.objects.filter(
                product=slow_product,
                alert_type=InventoryAlert.Type.SLOW_MOVING,
                is_active=True,
            ).exists()
        )

    @override_settings(OPENAI_API_KEY="")
    def test_ai_analysis_has_safe_local_fallback(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post(
            reverse("inventory-analyze"),
            {"days": 30, "focus": "الأصناف المعرضة للنفاد"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["source"], AIInsightReport.Source.LOCAL)
        self.assertEqual(response.data["ai_status"], "not_configured")
        self.assertTrue(response.data["summary"])
        self.assertEqual(AIInsightReport.objects.count(), 1)

    def test_order_sale_and_cancellation_are_recorded(self):
        self.product.stock = 6
        self.product.save(update_fields=["stock", "updated_at"])
        batch = InventoryBatch.objects.create(
            product=self.product,
            lot_number="LOT-SALE-01",
            quantity=6,
            unit_cost_cents=2500,
            received_at=timezone.localdate(),
            expires_at=timezone.localdate() + timedelta(days=60),
        )
        cart = Cart.objects.create(user=self.customer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        self.client.force_authenticate(self.customer)

        with self.captureOnCommitCallbacks(execute=True):
            checkout = self.client.post(
                reverse("order-list"),
                {
                    "payment_method": "cod",
                    "full_name": "عميل المخزون",
                    "phone": "0500000000",
                    "city": "الرياض",
                    "address": "شارع الاختبار",
                },
                format="json",
            )
        self.assertEqual(checkout.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get()
        batch.refresh_from_db()
        self.assertEqual(batch.quantity, 4)
        self.assertTrue(
            InventoryMovement.objects.filter(
                order=order,
                kind=InventoryMovement.Kind.SALE,
                quantity_delta=-2,
            ).exists()
        )

        with self.captureOnCommitCallbacks(execute=True):
            cancellation = self.client.post(reverse("order-cancel", args=[order.public_id]))
        self.assertEqual(cancellation.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        batch.refresh_from_db()
        self.assertEqual(self.product.stock, 6)
        self.assertEqual(batch.quantity, 6)
        self.assertTrue(
            InventoryMovement.objects.filter(
                order=order,
                kind=InventoryMovement.Kind.CANCELLATION,
                quantity_delta=2,
            ).exists()
        )
