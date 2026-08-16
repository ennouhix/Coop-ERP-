"""Tests du module contributions (apports des membres)."""

from __future__ import annotations

import uuid

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.catalog.models import Product, Unit
from apps.contributions.models import Contribution
from apps.cooperatives.models import Cooperative
from apps.members.services import create_member

User = get_user_model()

VALID_MEMBER_PAYLOAD = {
    "first_name": "Ahmed",
    "last_name": "Ouazzani",
    "phone_number": "0612345678",
    "cin": "AB123456",
}


class ContributionTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.cooperative = Cooperative.objects.create(
            name="Coopérative Argane Sud", slug="argane-sud"
        )
        self.other_cooperative = Cooperative.objects.create(name="Autre Coop", slug="autre")

        self.owner = User.objects.create_user(
            username="owner",
            email="owner@argane.ma",
            password="MotDePasseSolide123",
            cooperative=self.cooperative,
            role="owner",
        )
        self.staff = User.objects.create_user(
            username="staff",
            email="staff@argane.ma",
            password="MotDePasseSolide123",
            cooperative=self.cooperative,
            role="staff",
        )
        self.accountant = User.objects.create_user(
            username="acct",
            email="acct@argane.ma",
            password="MotDePasseSolide123",
            cooperative=self.cooperative,
            role="accountant",
        )
        self.foreign_user = User.objects.create_user(
            username="foreign",
            email="foreign@autre.ma",
            password="MotDePasseSolide123",
            cooperative=self.other_cooperative,
            role="owner",
        )

        self.member = create_member(cooperative=self.cooperative, **VALID_MEMBER_PAYLOAD)
        self.unit = Unit.objects.create(
            cooperative=self.cooperative, name="Kilogramme", symbol="kg", unit_type="weight"
        )
        self.product = Product.objects.create(
            cooperative=self.cooperative,
            sku="PRD-00001",
            name={"fr": "Huile d'argane", "ar": "زيت الأركان"},
            unit=self.unit,
        )
        self.list_url = reverse("contributions:list-create")

    def _auth(self, user) -> None:  # noqa: ANN001
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def _payload(self, **overrides) -> dict:
        payload = {
            "member_id": str(self.member.id),
            "product_id": str(self.product.id),
            "quantity": "120.5",
            "unit_price": "45.00",
            "campaign": "2026",
        }
        payload.update(overrides)
        return payload

    def test_staff_can_create_contribution(self) -> None:
        self._auth(self.staff)
        response = self.client.post(self.list_url, self._payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["total_amount"], "5422.50")
        self.assertEqual(response.data["product_name"], "Huile d'argane")
        self.assertEqual(Contribution.objects.count(), 1)

    def test_accountant_cannot_create_contribution(self) -> None:
        self._auth(self.accountant)
        response = self.client.post(self.list_url, self._payload())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_accountant_can_view_contributions(self) -> None:
        self._auth(self.staff)
        self.client.post(self.list_url, self._payload())
        self._auth(self.accountant)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_foreign_cooperative_gets_empty_list(self) -> None:
        self._auth(self.staff)
        self.client.post(self.list_url, self._payload())
        self._auth(self.foreign_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_mark_contribution_paid(self) -> None:
        self._auth(self.staff)
        created = self.client.post(self.list_url, self._payload()).data
        url = reverse("contributions:mark-paid", args=[created["id"]])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "paid")
        self.assertIsNotNone(response.data["payment_date"])

    def test_unknown_product_is_404(self) -> None:
        self._auth(self.staff)
        response = self.client.post(
            self.list_url, self._payload(product_id=str(uuid.uuid4())), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_negative_quantity_is_rejected(self) -> None:
        self._auth(self.staff)
        response = self.client.post(self.list_url, self._payload(quantity="-1"), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
