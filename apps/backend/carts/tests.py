from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Category, Product, ProductVariant
from commerce.models import Coupon


class CartApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="buyer", email="buyer@example.com", password="password123"
        )
        category = Category.objects.create(name="إلكترونيات", slug="electronics")
        self.product = Product.objects.create(
            category=category,
            name="سماعة",
            slug="headphones",
            sku="NOVA-CART-1",
            price_cents=10000,
            stock=3,
        )
        self.client.force_authenticate(self.user)

    def test_adds_product_to_cart(self):
        response = self.client.post(
            reverse("cart-item-collection"),
            {"product_id": self.product.id, "quantity": 2},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["subtotal_cents"], 20000)
        self.assertEqual(response.data["item_count"], 2)

    def test_variant_and_coupon_change_cart_quote(self):
        self.product.stock = 0
        self.product.save(update_fields=["stock"])
        variant = ProductVariant.objects.create(
            product=self.product,
            name="نسخة احترافية",
            sku="NOVA-CART-1-PRO",
            price_delta_cents=2000,
            stock=5,
        )
        response = self.client.post(
            reverse("cart-item-collection"),
            {"product_id": self.product.id, "variant_id": variant.id, "quantity": 2},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["subtotal_cents"], 24000)
        Coupon.objects.create(
            code="SAVE10",
            discount_type=Coupon.DiscountType.PERCENT,
            value=10,
            minimum_order_cents=1000,
        )
        response = self.client.post(reverse("cart-coupon"), {"code": "save10"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["discount_cents"], 2400)
        self.assertEqual(response.data["tax_cents"], 3240)
