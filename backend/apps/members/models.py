"""
Modèle Member — les adhérents (producteurs) de la coopérative.

Ne pas confondre avec `authentication.User` : un User est un EMPLOYÉ qui
se connecte au logiciel, un Member est un ADHÉRENT de la coopérative qui
n'a pas forcément de compte sur la plateforme.
"""

from __future__ import annotations

from decimal import Decimal

from django.db import models
from django.utils import timezone

from apps.core.models import TenantBaseModel
from apps.members.validators import cin_validator, phone_validator


class MemberType(models.TextChoices):
    INDIVIDUAL = "individual", "Personne physique"
    ENTITY = "entity", "Personne morale"


class MemberStatus(models.TextChoices):
    ACTIVE = "active", "Actif"
    SUSPENDED = "suspended", "Suspendu"
    INACTIVE = "inactive", "Inactif (parti)"


class Member(TenantBaseModel):
    """Un adhérent de la coopérative."""

    member_number = models.CharField(max_length=20, db_index=True, editable=False)

    member_type = models.CharField(
        max_length=15, choices=MemberType.choices, default=MemberType.INDIVIDUAL
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    cin = models.CharField("CIN", max_length=15, blank=True, validators=[cin_validator])

    phone_number = models.CharField(max_length=20, validators=[phone_validator])
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=500, blank=True)
    city = models.CharField(max_length=100, blank=True)

    birth_date = models.DateField(null=True, blank=True)
    join_date = models.DateField(default=timezone.localdate)
    status = models.CharField(
        max_length=15, choices=MemberStatus.choices, default=MemberStatus.ACTIVE
    )
    shares_count = models.PositiveIntegerField(
        default=0, help_text="Nombre de parts sociales détenues."
    )

    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Membre"
        verbose_name_plural = "Membres"
        ordering = ["last_name", "first_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["cooperative", "member_number"], name="unique_member_number_per_cooperative"
            ),
            models.UniqueConstraint(
                fields=["cooperative", "cin"],
                condition=~models.Q(cin=""),
                name="unique_cin_per_cooperative",
            ),
        ]
        indexes = [
            models.Index(fields=["cooperative", "status"]),
            models.Index(fields=["cooperative", "last_name", "first_name"]),
        ]

    def __str__(self) -> str:
        return f"{self.member_number} — {self.first_name} {self.last_name}"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class ShareTransactionType(models.TextChoices):
    SUBSCRIPTION = "subscription", "Souscription"
    REDEMPTION = "redemption", "Retrait"


class ShareTransaction(TenantBaseModel):
    """
    Mouvement de parts sociales : souscription ou retrait.

    Le capital social d'une coopérative marocaine est composé de parts
    sociales nominatives. Chaque mouvement est conservé (ledger) et le
    solde du membre est reflété sur `Member.shares_count`.
    """

    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="share_transactions")
    transaction_type = models.CharField(
        max_length=15,
        choices=ShareTransactionType.choices,
        default=ShareTransactionType.SUBSCRIPTION,
    )
    shares_count = models.PositiveIntegerField(
        help_text="Nombre de parts concernées par ce mouvement."
    )
    amount_per_share = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Valeur nominale d'une part au moment du mouvement (MAD).",
    )
    transaction_date = models.DateField(default=timezone.localdate)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Mouvement de parts sociales"
        verbose_name_plural = "Mouvements de parts sociales"
        indexes = [
            models.Index(fields=["cooperative", "member", "transaction_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.member} — {self.get_transaction_type_display()} {self.shares_count} part(s)"

    @property
    def total_amount(self) -> Decimal:
        return self.amount_per_share * self.shares_count
