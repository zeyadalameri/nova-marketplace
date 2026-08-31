import hashlib
import hmac
import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Address
from carts.models import Cart, CartItem
from catalog.models import Category, Product
from orders.models import Order

from .models import Notification, Payment, ReturnRequest, Shipment, WebhookEvent


class CommerceFlowTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="commerce-user", email="commerce@example.com", password="password123"
        )
        category = Category.objects.create(name="تقنية", slug="tech-commerce")
        self.product = Product.objects.create(
            category=category,
            name="منتج دفع",
            slug="payment-product",
            sku="PAY-1",
            price_cents=35000,
            stock=5,
        )
        self.address = Address.objects.create(
            user=self.user,
            full_name="عميل الدفع",
            phone="0500000000",
            city="الرياض",
            line1="شارع الدفع",
        )
        self.client.force_authenticate(self.user)

    def create_card_order(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        response = self.client.post(
            reverse("order-list"),
            {"payment_method": "card", "address_id": self.address.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return Order.objects.get(public_id=response.data["public_id"])

    def initiate(self, order, key="checkout-payment-1"):
        return self.client.post(
            reverse("order-initiate-payment", args=[order.public_id]),
            {},
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
        )

    def signed_webhook(self, payload):
        raw = json.dumps(payload, separators=(",", ":")).encode()
        signature = hmac.new(
            settings.PAYMENT_WEBHOOK_SECRET.encode(), raw, hashlib.sha256
        ).hexdigest()
        self.client.force_authenticate(user=None)
        return self.client.generic(
            "POST",
            reverse("payment-webhook"),
            raw,
            content_type="application/json",
            HTTP_X_NOVA_SIGNATURE=signature,
        )

    def test_card_payment_confirmation_is_idempotent_and_creates_shipment(self):
        order = self.create_card_order()
        response = self.initiate(order)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payment_id = response.data["public_id"]

        with self.captureOnCommitCallbacks(execute=True):
            confirmation = self.client.post(
                reverse("payment-sandbox-confirm", args=[payment_id]), {}, format="json"
            )
        self.assertEqual(confirmation.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertTrue(Shipment.objects.filter(order=order).exists())
        self.assertTrue(Notification.objects.filter(user=self.user, kind="payment").exists())

        repeat = self.client.post(
            reverse("payment-sandbox-confirm", args=[payment_id]), {}, format="json"
        )
        self.assertEqual(repeat.status_code, status.HTTP_200_OK)
        self.assertEqual(Payment.objects.filter(order=order).count(), 1)
        self.assertEqual(Shipment.objects.filter(order=order).count(), 1)

    def test_duplicate_payment_attempt_returns_the_existing_payment(self):
        order = self.create_card_order()
        first = self.initiate(order, "payment-attempt-1")
        second = self.initiate(order, "payment-attempt-2")

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(first.data["public_id"], second.data["public_id"])
        self.assertEqual(Payment.objects.filter(order=order).count(), 1)

    def test_payment_cannot_start_or_complete_after_cancellation(self):
        order = self.create_card_order()
        initiated = self.initiate(order, "cancelled-payment")
        payment_id = initiated.data["public_id"]

        cancellation = self.client.post(reverse("order-cancel", args=[order.public_id]))
        self.assertEqual(cancellation.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.initiate(order, "cancelled-payment-retry").status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        confirmation = self.client.post(
            reverse("payment-sandbox-confirm", args=[payment_id]), {}, format="json"
        )
        self.assertEqual(confirmation.status_code, status.HTTP_400_BAD_REQUEST)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(order.payment_status, Order.PaymentStatus.FAILED)

    def test_payment_cannot_start_again_after_order_is_paid(self):
        order = self.create_card_order()
        initiated = self.initiate(order, "paid-payment")
        confirmation = self.client.post(
            reverse("payment-sandbox-confirm", args=[initiated.data["public_id"]]),
            {},
            format="json",
        )
        self.assertEqual(confirmation.status_code, status.HTTP_200_OK)

        retry = self.initiate(order, "paid-payment-retry")
        self.assertEqual(retry.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Payment.objects.filter(order=order).count(), 1)

    def test_webhook_rejects_invalid_signature(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            reverse("payment-webhook"),
            {"event_id": "bad", "payment_id": "00000000-0000-0000-0000-000000000000"},
            format="json",
            HTTP_X_NOVA_SIGNATURE="invalid",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_signed_webhook_is_processed_once(self):
        order = self.create_card_order()
        initiated = self.initiate(order, "webhook-payment-1")
        payment_id = initiated.data["public_id"]
        payload = {
            "event_id": "evt-100",
            "payment_id": str(payment_id),
            "type": "payment.succeeded",
            "amount_cents": initiated.data["amount_cents"],
            "currency": initiated.data["currency"],
        }
        response = self.signed_webhook(payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.signed_webhook(payload)
        self.assertFalse(response.data["processed"])
        self.assertEqual(WebhookEvent.objects.filter(event_id="evt-100").count(), 1)
        self.assertEqual(Shipment.objects.filter(order=order).count(), 1)

    def test_webhook_rejects_wrong_type_amount_and_currency(self):
        order = self.create_card_order()
        initiated = self.initiate(order, "validated-webhook-payment")
        payment_id = initiated.data["public_id"]
        valid = {
            "payment_id": str(payment_id),
            "type": "payment.succeeded",
            "amount_cents": initiated.data["amount_cents"],
            "currency": initiated.data["currency"],
        }
        invalid_payloads = [
            {**valid, "event_id": "evt-wrong-type", "type": "payment.failed"},
            {**valid, "event_id": "evt-wrong-amount", "amount_cents": valid["amount_cents"] + 1},
            {**valid, "event_id": "evt-wrong-currency", "currency": "USD"},
        ]
        for payload in invalid_payloads:
            with self.subTest(event_id=payload["event_id"]):
                response = self.signed_webhook(payload)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        order.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertFalse(Shipment.objects.filter(order=order).exists())

    def test_delivered_order_accepts_return_request(self):
        order = Order.objects.create(
            user=self.user,
            full_name="عميل",
            phone="0500000000",
            city="الرياض",
            address="عنوان",
            status=Order.Status.DELIVERED,
            invoice_number="NOVA-RETURN-1",
        )
        response = self.client.post(
            reverse("return-request-list"),
            {"order_id": str(order.public_id), "reason": "المنتج غير مناسب"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReturnRequest.objects.get().user, self.user)
