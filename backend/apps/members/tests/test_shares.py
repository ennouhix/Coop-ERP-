"""Tests des parts sociales (module members)."""

from __future__ import annotations

import uuid

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.cooperatives.models import Cooperative
from apps.members.models import ShareTransaction
from apps.members.services import create_member

User = get_user_model()

VALID_MEMBER_PAYLOAD = {
    "first_name": "Ahmed",
    "last_name": "Ouazzani",
    "phone_number": "0612345678",
    "cin": "AB123456",
}


class ShareTransactionTestCase(APITestCase):
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
        self.url = reverse("members:shares-list-create")

    def _auth(self, user) -> None:  # noqa: ANN001
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def _payload(self, **overrides) -> dict:
        payload = {
            "member_id": str(self.member.id),
            "transaction_type": "subscription",
            "shares_count": 10,
            "amount_per_share": "100.00",
        }
        payload.update(overrides)
        return payload

    def test_staff_can_subscribe_shares(self) -> None:
        self._auth(self.staff)
        response = self.client.post(self.url, self._payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["total_amount"], "1000.00")
        self.member.refresh_from_db()
        self.assertEqual(self.member.shares_count, 10)
        self.assertEqual(ShareTransaction.objects.count(), 1)

    def test_redeem_shares_decreases_balance(self) -> None:
        self._auth(self.staff)
        self.client.post(self.url, self._payload())
        response = self.client.post(
            self.url, self._payload(transaction_type="redemption", shares_count=4), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.member.refresh_from_db()
        self.assertEqual(self.member.shares_count, 6)

    def test_redeem_more_than_held_is_rejected(self) -> None:
        self._auth(self.staff)
        response = self.client.post(
            self.url, self._payload(transaction_type="redemption", shares_count=5), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"]["message"],
            "Ce membre ne détient que 0 part(s) : impossible d'en retirer 5.",
        )
        self.member.refresh_from_db()
        self.assertEqual(self.member.shares_count, 0)

    def test_negative_shares_count_is_rejected(self) -> None:
        self._auth(self.staff)
        response = self.client.post(self.url, self._payload(shares_count=-3), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_accountant_cannot_create_share_transaction(self) -> None:
        self._auth(self.accountant)
        response = self.client.post(self.url, self._payload())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_accountant_can_view_transactions(self) -> None:
        self._auth(self.staff)
        self.client.post(self.url, self._payload())
        self._auth(self.accountant)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_foreign_cooperative_gets_empty_list(self) -> None:
        self._auth(self.staff)
        self.client.post(self.url, self._payload())
        self._auth(self.foreign_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_member_from_another_cooperative_is_404(self) -> None:
        other_member = create_member(cooperative=self.other_cooperative, **VALID_MEMBER_PAYLOAD)
        self._auth(self.staff)
        response = self.client.post(
            self.url, self._payload(member_id=str(other_member.id)), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unknown_member_is_404(self) -> None:
        self._auth(self.staff)
        response = self.client.post(
            self.url, self._payload(member_id=str(uuid.uuid4())), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
