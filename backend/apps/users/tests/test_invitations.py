"""
Tests du flux d'invitation : création, acceptation, garde-fous.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.cooperatives.models import Cooperative
from apps.users.models import Invitation, InvitationStatus

User = get_user_model()


class InvitationTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.cooperative = Cooperative.objects.create(name="Coopérative Argane", slug="argane")
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
        self.invitations_url = reverse("users:invitation-list-create")
        self.accept_url = reverse("users:invitation-accept")

    def _auth(self, user) -> None:  # noqa: ANN001
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_owner_can_invite_new_member(self) -> None:
        self._auth(self.owner)
        response = self.client.post(
            self.invitations_url, {"email": "nouveau@test.ma", "role": "staff"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("nouveau@test.ma", mail.outbox[0].to)

    def test_staff_cannot_invite(self) -> None:
        self._auth(self.staff)
        response = self.client.post(
            self.invitations_url, {"email": "nouveau@test.ma", "role": "staff"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_invite_existing_active_member(self) -> None:
        self._auth(self.owner)
        response = self.client.post(
            self.invitations_url, {"email": "staff@argane.ma", "role": "admin"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_duplicate_pending_invitation(self) -> None:
        self._auth(self.owner)
        self.client.post(self.invitations_url, {"email": "nouveau@test.ma", "role": "staff"})
        response = self.client.post(
            self.invitations_url, {"email": "nouveau@test.ma", "role": "admin"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_cannot_invite_owner(self) -> None:
        admin = User.objects.create_user(
            username="admin",
            email="admin@argane.ma",
            password="MotDePasseSolide123",
            cooperative=self.cooperative,
            role="admin",
        )
        self._auth(admin)
        response = self.client.post(
            self.invitations_url, {"email": "nouveauowner@test.ma", "role": "owner"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_accept_invitation_creates_active_user_with_correct_role(self) -> None:
        self._auth(self.owner)
        self.client.post(self.invitations_url, {"email": "nouveau@test.ma", "role": "admin"})
        invitation = Invitation.objects.get(email="nouveau@test.ma")

        self.client.credentials()  # endpoint public, retire l'auth
        response = self.client.post(
            self.accept_url,
            {
                "token": invitation.token,
                "first_name": "Karim",
                "last_name": "Bennani",
                "password": "MotDePasseSolide456",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)

        new_user = User.objects.get(email="nouveau@test.ma")
        self.assertEqual(new_user.role, "admin")
        self.assertEqual(new_user.cooperative_id, self.cooperative.id)

        invitation.refresh_from_db()
        self.assertEqual(invitation.status, InvitationStatus.ACCEPTED)

    def test_accepted_invitation_token_cannot_be_reused(self) -> None:
        self._auth(self.owner)
        self.client.post(self.invitations_url, {"email": "nouveau@test.ma", "role": "staff"})
        invitation = Invitation.objects.get(email="nouveau@test.ma")

        self.client.credentials()
        payload = {
            "token": invitation.token,
            "first_name": "A",
            "last_name": "B",
            "password": "MotDePasseSolide456",
        }
        self.client.post(self.accept_url, payload)

        second_attempt = self.client.post(
            self.accept_url,
            {**payload, "password": "AutreMotDePasse789"},
        )
        self.assertEqual(second_attempt.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_can_cancel_pending_invitation(self) -> None:
        self._auth(self.owner)
        self.client.post(self.invitations_url, {"email": "nouveau@test.ma", "role": "staff"})
        invitation = Invitation.objects.get(email="nouveau@test.ma")

        url = reverse("users:invitation-cancel", args=[invitation.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        invitation.refresh_from_db()
        self.assertEqual(invitation.status, InvitationStatus.CANCELLED)

    def test_cancelled_invitation_email_can_be_reinvited(self) -> None:
        self._auth(self.owner)
        self.client.post(self.invitations_url, {"email": "nouveau@test.ma", "role": "staff"})
        invitation = Invitation.objects.get(email="nouveau@test.ma")
        self.client.delete(reverse("users:invitation-cancel", args=[invitation.id]))

        response = self.client.post(
            self.invitations_url, {"email": "nouveau@test.ma", "role": "admin"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
