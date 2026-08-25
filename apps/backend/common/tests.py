from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class SecurityBoundaryTests(APITestCase):
    def test_health_is_public_but_customer_data_requires_authentication(self):
        self.assertEqual(self.client.get(reverse("health")).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(reverse("cart-detail")).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(reverse("order-list")).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.client.get(reverse("notification-list")).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_users_cannot_read_each_others_addresses(self):
        first = get_user_model().objects.create_user("first", "first@example.com", "password123")
        second = get_user_model().objects.create_user("second", "second@example.com", "password123")
        self.client.force_authenticate(first)
        created = self.client.post(
            reverse("address-list"),
            {"full_name": "الأول", "phone": "0500000000", "city": "الرياض", "line1": "عنوان"},
            format="json",
        )
        self.client.force_authenticate(second)
        self.assertEqual(
            self.client.get(reverse("address-detail", args=[created.data["id"]])).status_code,
            status.HTTP_404_NOT_FOUND,
        )
