from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Address


class AccountApiTests(APITestCase):
    def test_register_and_get_token(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "buyer",
                "email": "buyer@example.com",
                "password": "StrongPassword123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            reverse("token-obtain-pair"),
            {"username": "buyer", "password": "StrongPassword123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_user_can_manage_own_addresses(self):
        user = self._create_user("address-owner")
        self.client.force_authenticate(user)
        response = self.client.post(
            reverse("address-list"),
            {
                "label": "المنزل",
                "full_name": "عميل نوفا",
                "phone": "0500000000",
                "country_code": "sa",
                "city": "الرياض",
                "line1": "حي الاختبار",
                "is_default": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Address.objects.get().country_code, "SA")

    def test_logout_blacklists_refresh_token_and_is_idempotent(self):
        self._create_user("logout-user")
        token_response = self.client.post(
            reverse("token-obtain-pair"),
            {"username": "logout-user", "password": "StrongPassword123!"},
            format="json",
        )
        refresh = token_response.data["refresh"]

        first = self.client.post(reverse("logout"), {"refresh": refresh}, format="json")
        second = self.client.post(reverse("logout"), {"refresh": refresh}, format="json")
        refresh_attempt = self.client.post(
            reverse("token-refresh"), {"refresh": refresh}, format="json"
        )

        self.assertEqual(first.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(second.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(refresh_attempt.status_code, status.HTTP_401_UNAUTHORIZED)

    @staticmethod
    def _create_user(username):
        from django.contrib.auth import get_user_model

        return get_user_model().objects.create_user(
            username=username, email=f"{username}@example.com", password="StrongPassword123!"
        )
