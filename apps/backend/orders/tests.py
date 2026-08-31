import uuid
from datetime import timedelta
from threading import Barrier, Lock, Thread
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from carts.models import Cart, CartItem
from catalog.models import Category, Product
from accounts.models import Address
from commerce.models import Coupon, CouponRedemption, Payment

from .models import Order
from .services import release_expired_reservations


class OrderApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="buyer", email="buyer@example.com", password="password123"
        )
        category = Category.objects.create(name="إلكترونيات", slug="electronics")
        self.product = Product.objects.create(
            category=category,
            name="سماعة",
            slug="headphones-order",
            sku="NOVA-ORDER-1",
            price_cents=20000,
            stock=3,
        )
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        self.client.force_authenticate(self.user)

    def test_checkout_decrements_stock_and_clears_cart(self):
        response = self.client.post(
            reverse("order-list"),
            {
                "payment_method": "cod",
                "full_name": "عميل تجريبي",
                "phone": "0500000000",
                "city": "الرياض",
                "address": "شارع الاختبار",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tax_cents"], 6000)
        self.assertEqual(response.data["total_cents"], 46000)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)
        self.assertFalse(CartItem.objects.exists())
        self.assertEqual(Order.objects.count(), 1)

    def test_checkout_rejects_insufficient_stock(self):
        self.product.stock = 1
        self.product.save(update_fields=["stock"])
        response = self.client.post(
            reverse("order-list"),
            {
                "payment_method": "cod",
                "full_name": "عميل تجريبي",
                "phone": "0500000000",
                "city": "الرياض",
                "address": "شارع الاختبار",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_with_saved_address_and_coupon(self):
        address = Address.objects.create(
            user=self.user,
            full_name="عميل العنوان",
            phone="0511111111",
            city="جدة",
            line1="حي البحر",
            is_default=True,
        )
        Coupon.objects.create(
            code="ORDER10",
            discount_type=Coupon.DiscountType.PERCENT,
            value=10,
            minimum_order_cents=1000,
        )
        response = self.client.post(
            reverse("order-list"),
            {
                "payment_method": "card",
                "address_id": address.id,
                "coupon_code": "order10",
                "currency": "SAR",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["discount_cents"], 4000)
        self.assertEqual(response.data["tax_cents"], 5400)
        self.assertTrue(response.data["invoice_number"].startswith("NOVA-"))
        self.assertEqual(response.data["city"], "جدة")
        self.assertEqual(CouponRedemption.objects.count(), 1)

    def test_checkout_idempotency_returns_the_original_order(self):
        payload = {
            "payment_method": "cod",
            "full_name": "عميل تجريبي",
            "phone": "0500000000",
            "city": "الرياض",
            "address": "شارع الاختبار",
        }
        headers = {"HTTP_IDEMPOTENCY_KEY": "checkout-attempt-1"}
        first = self.client.post(reverse("order-list"), payload, format="json", **headers)
        second = self.client.post(reverse("order-list"), payload, format="json", **headers)

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data["public_id"], second.data["public_id"])
        self.assertEqual(Order.objects.count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)

    def test_cancel_missing_order_returns_not_found(self):
        response = self.client.post(
            reverse("order-cancel", args=[uuid.uuid4()]),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_expired_card_reservation_releases_inventory_once(self):
        response = self.client.post(
            reverse("order-list"),
            {
                "payment_method": "card",
                "full_name": "عميل حجز",
                "phone": "0500000000",
                "city": "الرياض",
                "address": "شارع الاختبار",
            },
            format="json",
        )
        order = Order.objects.get(public_id=response.data["public_id"])
        payment_response = self.client.post(
            reverse("order-initiate-payment", args=[order.public_id]),
            {},
            format="json",
            HTTP_IDEMPOTENCY_KEY="expiring-reservation-payment",
        )
        self.assertEqual(payment_response.status_code, status.HTTP_201_CREATED)
        Order.objects.filter(pk=order.pk).update(
            reservation_expires_at=timezone.now() - timedelta(seconds=1)
        )

        self.assertEqual(release_expired_reservations(), 1)
        self.assertEqual(release_expired_reservations(), 0)

        order.refresh_from_db()
        self.product.refresh_from_db()
        payment = Payment.objects.get(order=order)
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(order.payment_status, Order.PaymentStatus.FAILED)
        self.assertIsNotNone(order.inventory_released_at)
        self.assertEqual(payment.status, Payment.Status.FAILED)
        self.assertEqual(self.product.stock, 3)

    def test_expired_bank_transfer_reservation_releases_inventory_without_payment(self):
        response = self.client.post(
            reverse("order-list"),
            {
                "payment_method": "bank",
                "full_name": "عميل تحويل",
                "phone": "0500000000",
                "city": "الرياض",
                "address": "شارع الاختبار",
            },
            format="json",
        )
        order = Order.objects.get(public_id=response.data["public_id"])
        self.assertIsNotNone(order.reservation_expires_at)
        Order.objects.filter(pk=order.pk).update(
            reservation_expires_at=timezone.now() - timedelta(seconds=1)
        )

        self.assertEqual(release_expired_reservations(), 1)
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(order.payment_status, Order.PaymentStatus.FAILED)
        self.assertEqual(self.product.stock, 3)
        self.assertFalse(Payment.objects.filter(order=order).exists())


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row-level locking")
class ConcurrentInventoryTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        category = Category.objects.create(name="تزامن", slug="concurrent-orders")
        self.product = Product.objects.create(
            category=category,
            name="آخر وحدة",
            slug="last-unit",
            sku="LAST-UNIT-1",
            price_cents=1000,
            stock=1,
        )
        self.users = []
        for index in range(2):
            user = get_user_model().objects.create_user(
                username=f"concurrent-{index}",
                email=f"concurrent-{index}@example.com",
                password="password123",
            )
            cart = Cart.objects.create(user=user)
            CartItem.objects.create(cart=cart, product=self.product, quantity=1)
            self.users.append(user)

    def test_two_concurrent_checkouts_cannot_sell_the_last_unit_twice(self):
        barrier = Barrier(2)
        result_lock = Lock()
        statuses = []
        errors = []

        def checkout(user_id):
            close_old_connections()
            try:
                user = get_user_model().objects.get(pk=user_id)
                client = APIClient()
                client.force_authenticate(user)
                barrier.wait(timeout=5)
                response = client.post(
                    reverse("order-list"),
                    {
                        "payment_method": "cod",
                        "full_name": "عميل متزامن",
                        "phone": "0500000000",
                        "city": "الرياض",
                        "address": "شارع الاختبار",
                    },
                    format="json",
                )
                with result_lock:
                    statuses.append(response.status_code)
            except Exception as exc:  # pragma: no cover - diagnostic path for threaded test
                with result_lock:
                    errors.append(exc)
            finally:
                close_old_connections()

        threads = [Thread(target=checkout, args=(user.pk,)) for user in self.users]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        self.assertFalse(errors)
        self.assertEqual(sorted(statuses), [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 0)
        self.assertEqual(Order.objects.count(), 1)
