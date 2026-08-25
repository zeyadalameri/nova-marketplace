from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from django.contrib.auth import get_user_model

from .models import Category, Product, ProductVariant, Review


class CatalogApiTests(APITestCase):
    def setUp(self):
        category = Category.objects.create(name="إلكترونيات", slug="electronics")
        Product.objects.create(
            category=category,
            name="سماعة لاسلكية",
            slug="wireless-headphones",
            sku="NOVA-001",
            price_cents=29900,
            stock=10,
            is_featured=True,
        )

    def test_lists_and_searches_products(self):
        response = self.client.get(reverse("product-list"), {"q": "سماعة"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["price"], "299.00")

    def test_product_variants_and_reviews_are_available(self):
        product = Product.objects.get()
        ProductVariant.objects.create(
            product=product,
            name="أسود",
            sku="NOVA-001-BLACK",
            attributes={"color": "black"},
            price_delta_cents=2000,
            stock=4,
        )
        detail = self.client.get(reverse("product-detail", args=[product.slug]))
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["variants"][0]["price_cents"], 31900)

        user = get_user_model().objects.create_user(
            username="reviewer", email="reviewer@example.com", password="password123"
        )
        self.client.force_authenticate(user)
        response = self.client.post(
            reverse("review-list"),
            {"product_slug": product.slug, "rating": 5, "title": "ممتاز", "comment": "جودة رائعة"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)
