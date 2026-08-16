"""
Tests du module partners.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.cooperatives.models import Cooperative
from apps.partners.services import create_partner

User = get_user_model()

VALID_CUSTOMER_PAYLOAD = {
    "is_customer": True,
    "is_supplier": False,
    "name": "Épicerie Al Baraka",
    "phone_number": "0612345678",
}


class PartnerTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.cooperative = Cooperative.objects.create(
            name="Coopérative Argane Sud", slug="argane-sud"
        )
        self.other_cooperative = Cooperative.objects.create(name="Autre Coop", slug="autre")

        self.staff = User.objects.create_user(
            username="staff",
            email="staff@argane.ma",
            password="MotDePasseSolide123",
            cooperative=self.cooperative,
            role="staff",
        )
        self.foreign_user = User.objects.create_user(
            username="foreign",
            email="foreign@autre.ma",
            password="MotDePasseSolide123",
            cooperative=self.other_cooperative,
            role="owner",
        )

        self.list_url = reverse("partners:list-create")

    def _auth(self, user) -> None:  # noqa: ANN001
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_staff_can_create_customer(self) -> None:
        self._auth(self.staff)
        response = self.client.post(self.list_url, VALID_CUSTOMER_PAYLOAD)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["code"], "PART-0001")

    def test_partner_codes_are_sequential(self) -> None:
        self._auth(self.staff)
        self.client.post(self.list_url, VALID_CUSTOMER_PAYLOAD)
        second = {**VALID_CUSTOMER_PAYLOAD, "name": "Autre Client"}
        response = self.client.post(self.list_url, second)
        self.assertEqual(response.data["code"], "PART-0002")

    def test_cannot_create_partner_neither_customer_nor_supplier(self) -> None:
        self._auth(self.staff)
        invalid = {**VALID_CUSTOMER_PAYLOAD, "is_customer": False, "is_supplier": False}
        response = self.client.post(self.list_url, invalid)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partner_can_be_both_customer_and_supplier(self) -> None:
        self._auth(self.staff)
        both = {**VALID_CUSTOMER_PAYLOAD, "is_supplier": True}
        response = self.client.post(self.list_url, both)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_customer"])
        self.assertTrue(response.data["is_supplier"])

    def test_duplicate_ice_in_same_cooperative_rejected(self) -> None:
        create_partner(
            cooperative=self.cooperative, ice="001234567000012", **VALID_CUSTOMER_PAYLOAD
        )
        self._auth(self.staff)
        duplicate = {**VALID_CUSTOMER_PAYLOAD, "name": "Autre", "ice": "001234567000012"}
        response = self.client.post(self.list_url, duplicate)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_cannot_see_partners_from_other_cooperative(self) -> None:
        create_partner(cooperative=self.cooperative, **VALID_CUSTOMER_PAYLOAD)
        self._auth(self.foreign_user)
        response = self.client.get(self.list_url)
        results = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(results), 0)

    def test_filter_by_is_supplier(self) -> None:
        create_partner(cooperative=self.cooperative, **VALID_CUSTOMER_PAYLOAD)
        create_partner(
            cooperative=self.cooperative,
            is_customer=False,
            is_supplier=True,
            name="Fournisseur Emballages",
            phone_number="0611111111",
        )
        self._auth(self.staff)
        response = self.client.get(self.list_url, {"is_supplier": "true"})
        results = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Fournisseur Emballages")

    def test_search_by_name(self) -> None:
        create_partner(cooperative=self.cooperative, **VALID_CUSTOMER_PAYLOAD)
        self._auth(self.staff)
        response = self.client.get(self.list_url, {"search": "Baraka"})
        results = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(results), 1)

    def test_deactivate_and_reactivate_partner(self) -> None:
        partner = create_partner(cooperative=self.cooperative, **VALID_CUSTOMER_PAYLOAD)
        self._auth(self.staff)

        deactivate_url = reverse("partners:deactivate", args=[partner.id])
        response = self.client.post(deactivate_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        partner.refresh_from_db()
        self.assertFalse(partner.is_active)

        reactivate_url = reverse("partners:reactivate", args=[partner.id])
        response = self.client.post(reactivate_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        partner.refresh_from_db()
        self.assertTrue(partner.is_active)

    def test_update_payment_terms(self) -> None:
        partner = create_partner(cooperative=self.cooperative, **VALID_CUSTOMER_PAYLOAD)
        self._auth(self.staff)
        url = reverse("partners:detail", args=[partner.id])
        response = self.client.patch(url, {"payment_terms_days": 30})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        partner.refresh_from_db()
        self.assertEqual(partner.payment_terms_days, 30)

    def test_update_cannot_remove_both_customer_and_supplier_flags(self) -> None:
        partner = create_partner(cooperative=self.cooperative, **VALID_CUSTOMER_PAYLOAD)
        self._auth(self.staff)
        url = reverse("partners:detail", args=[partner.id])
        response = self.client.patch(url, {"is_customer": False})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_code_immutable_on_update(self) -> None:
        partner = create_partner(cooperative=self.cooperative, **VALID_CUSTOMER_PAYLOAD)
        self._auth(self.staff)
        url = reverse("partners:detail", args=[partner.id])
        response = self.client.patch(url, {"code": "HACKED-9999"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        partner.refresh_from_db()
        self.assertEqual(partner.code, "PART-0001")
