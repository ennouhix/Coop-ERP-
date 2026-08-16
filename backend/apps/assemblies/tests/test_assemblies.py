"""Tests du module assemblies (assemblées générales)."""

from __future__ import annotations

import uuid

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.assemblies.models import Assembly, AssemblyAttendance
from apps.cooperatives.models import Cooperative
from apps.members.services import create_member

User = get_user_model()

VALID_MEMBER_PAYLOAD = {
    "first_name": "Ahmed",
    "last_name": "Ouazzani",
    "phone_number": "0612345678",
    "cin": "AB123456",
}


class AssemblyTestCase(APITestCase):
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
        self.list_url = reverse("assemblies:list-create")

    def _auth(self, user) -> None:  # noqa: ANN001
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def _payload(self, **overrides) -> dict:
        payload = {
            "title": "Assemblée générale annuelle",
            "assembly_type": "ordinary",
            "scheduled_date": "2026-05-15",
            "quorum_percent": "50.00",
            "agenda": "Approbation des comptes",
        }
        payload.update(overrides)
        return payload

    def test_staff_can_create_assembly(self) -> None:
        self._auth(self.staff)
        response = self.client.post(self.list_url, self._payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["attendances_count"], 0)

    def test_accountant_cannot_create_assembly(self) -> None:
        self._auth(self.accountant)
        response = self.client.post(self.list_url, self._payload())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_accountant_can_view_assemblies(self) -> None:
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

    def test_register_attendance_and_vote(self) -> None:
        self._auth(self.staff)
        assembly = Assembly.objects.create(
            cooperative=self.cooperative, title="AG annuelle", scheduled_date="2026-05-15"
        )
        url = reverse("assemblies:attendance", args=[assembly.id])
        response = self.client.post(
            url,
            {"member_id": str(self.member.id), "attendance_status": "present", "vote": "for"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AssemblyAttendance.objects.count(), 1)

        list_response = self.client.get(url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data["results"]), 1)

        detail = self.client.get(reverse("assemblies:detail", args=[assembly.id]))
        self.assertEqual(detail.data["attendances_count"], 1)
        self.assertEqual(detail.data["present_count"], 1)

    def test_register_attendance_is_an_upsert(self) -> None:
        self._auth(self.staff)
        assembly = Assembly.objects.create(
            cooperative=self.cooperative, title="AG annuelle", scheduled_date="2026-05-15"
        )
        url = reverse("assemblies:attendance", args=[assembly.id])
        self.client.post(url, {"member_id": str(self.member.id), "vote": "for"}, format="json")
        response = self.client.post(
            url, {"member_id": str(self.member.id), "vote": "against"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AssemblyAttendance.objects.count(), 1)
        self.assertEqual(AssemblyAttendance.objects.get().vote, "against")

    def test_member_from_another_cooperative_is_404(self) -> None:
        other_member = create_member(cooperative=self.other_cooperative, **VALID_MEMBER_PAYLOAD)
        self._auth(self.staff)
        assembly = Assembly.objects.create(
            cooperative=self.cooperative, title="AG annuelle", scheduled_date="2026-05-15"
        )
        url = reverse("assemblies:attendance", args=[assembly.id])
        response = self.client.post(url, {"member_id": str(other_member.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_attendance_of_unknown_assembly_is_404(self) -> None:
        self._auth(self.staff)
        url = reverse("assemblies:attendance", args=[uuid.uuid4()])
        response = self.client.post(url, {"member_id": str(self.member.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
