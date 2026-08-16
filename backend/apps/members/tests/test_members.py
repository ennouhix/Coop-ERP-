"""
Tests du module members.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.cooperatives.models import Cooperative
from apps.members.services import create_member

User = get_user_model()

VALID_MEMBER_PAYLOAD = {
    "first_name": "Ahmed",
    "last_name": "Ouazzani",
    "phone_number": "0612345678",
    "cin": "AB123456",
}


class MemberTestCase(APITestCase):
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

        self.list_url = reverse("members:list-create")

    def _auth(self, user) -> None:  # noqa: ANN001
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_staff_can_create_member(self) -> None:
        self._auth(self.staff)
        response = self.client.post(self.list_url, VALID_MEMBER_PAYLOAD)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["member_number"], "ARG-0001")

    def test_member_numbers_are_sequential(self) -> None:
        self._auth(self.staff)
        self.client.post(self.list_url, VALID_MEMBER_PAYLOAD)
        second_payload = {**VALID_MEMBER_PAYLOAD, "cin": "CD654321", "first_name": "Yassine"}
        response = self.client.post(self.list_url, second_payload)
        self.assertEqual(response.data["member_number"], "ARG-0002")

    def test_accountant_cannot_create_member(self) -> None:
        self._auth(self.accountant)
        response = self.client.post(self.list_url, VALID_MEMBER_PAYLOAD)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_accountant_can_view_members(self) -> None:
        create_member(cooperative=self.cooperative, **VALID_MEMBER_PAYLOAD)
        self._auth(self.accountant)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_duplicate_cin_in_same_cooperative_is_rejected(self) -> None:
        create_member(cooperative=self.cooperative, **VALID_MEMBER_PAYLOAD)
        self._auth(self.staff)
        duplicate = {**VALID_MEMBER_PAYLOAD, "first_name": "Autre Personne"}
        response = self.client.post(self.list_url, duplicate)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_cin_allowed_in_different_cooperatives(self) -> None:
        create_member(cooperative=self.cooperative, **VALID_MEMBER_PAYLOAD)
        member2 = create_member(cooperative=self.other_cooperative, **VALID_MEMBER_PAYLOAD)
        self.assertEqual(member2.member_number, "AUT-0001")

    def test_invalid_cin_format_is_rejected(self) -> None:
        self._auth(self.staff)
        invalid = {**VALID_MEMBER_PAYLOAD, "cin": "12345"}
        response = self.client.post(self.list_url, invalid)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_by_name(self) -> None:
        create_member(cooperative=self.cooperative, **VALID_MEMBER_PAYLOAD)
        self._auth(self.staff)
        response = self.client.get(self.list_url, {"search": "Ouazzani"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(results), 1)

    def test_filter_by_status(self) -> None:
        member = create_member(cooperative=self.cooperative, **VALID_MEMBER_PAYLOAD)
        member.status = "suspended"
        member.save(update_fields=["status"])
        self._auth(self.staff)
        response = self.client.get(self.list_url, {"status": "active"})
        results = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(results), 0)

    def test_user_cannot_see_members_from_other_cooperative(self) -> None:
        create_member(cooperative=self.cooperative, **VALID_MEMBER_PAYLOAD)
        self._auth(self.foreign_user)
        response = self.client.get(self.list_url)
        results = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(results), 0)

    def test_deactivate_member(self) -> None:
        member = create_member(cooperative=self.cooperative, **VALID_MEMBER_PAYLOAD)
        self._auth(self.staff)
        url = reverse("members:deactivate", args=[member.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        member.refresh_from_db()
        self.assertEqual(member.status, "inactive")
        self.assertFalse(member.is_active)

    def test_reactivate_member(self) -> None:
        member = create_member(cooperative=self.cooperative, **VALID_MEMBER_PAYLOAD)
        member.is_active = False
        member.status = "inactive"
        member.save(update_fields=["is_active", "status"])

        self._auth(self.staff)
        url = reverse("members:reactivate", args=[member.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        member.refresh_from_db()
        self.assertEqual(member.status, "active")
        self.assertTrue(member.is_active)

    def test_update_member_info(self) -> None:
        member = create_member(cooperative=self.cooperative, **VALID_MEMBER_PAYLOAD)
        self._auth(self.owner)
        url = reverse("members:detail", args=[member.id])
        response = self.client.patch(url, {"phone_number": "0699999999"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        member.refresh_from_db()
        self.assertEqual(member.phone_number, "0699999999")

    def test_member_number_immutable_on_update(self) -> None:
        member = create_member(cooperative=self.cooperative, **VALID_MEMBER_PAYLOAD)
        self._auth(self.owner)
        url = reverse("members:detail", args=[member.id])
        response = self.client.patch(url, {"member_number": "HACKED-9999"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        member.refresh_from_db()
        self.assertEqual(member.member_number, "ARG-0001")

    def test_deactivated_member_still_visible_in_list_via_status_filter(self) -> None:
        """
        Bug réel corrigé : un membre désactivé (is_active=False) devenait
        invisible PARTOUT via le manager par défaut filtré, y compris avec
        ?status=inactive — donnant l'impression trompeuse d'une suppression
        alors que la ligne existe toujours en base.
        """
        member = create_member(cooperative=self.cooperative, **VALID_MEMBER_PAYLOAD)
        self._auth(self.staff)
        self.client.post(reverse("members:deactivate", args=[member.id]))

        response = self.client.get(self.list_url, {"status": "inactive"})
        results = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], str(member.id))

    def test_deactivated_member_detail_page_still_accessible(self) -> None:
        """Sans ce correctif, cette requête renvoyait 404 après désactivation."""
        member = create_member(cooperative=self.cooperative, **VALID_MEMBER_PAYLOAD)
        self._auth(self.staff)
        self.client.post(reverse("members:deactivate", args=[member.id]))

        response = self.client.get(reverse("members:detail", args=[member.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "inactive")
