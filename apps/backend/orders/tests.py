import uuid

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from carts.models import Cart, CartItem
from catalog.models import Category, Product
from accounts.models import Address
from commerce.models import Coupon, CouponRedemption

from .models import Order


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
