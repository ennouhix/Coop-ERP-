"""
Modèles du module Comptabilité / Trésorerie.

Architecture comptable :
- Account      : un compte du plan comptable (PCM marocain)
- Journal      : journal comptable (ventes, achats, caisse, banque, OD)
- AccountingEntry : en-tête d'une écriture comptable (brouillon → validée)
- AccountingEntryLine : ligne débit/crédit d'une écriture

Règle fondamentale : Σ débit == Σ crédit (vérifiée à la validation dans services.py).
Toutes les tables héritent de TenantBaseModel pour l'isolation multi-tenant.
"""
from __future__ import annotations

from decimal import Decimal

from django.db import models

from apps.core.fields import TranslatedField, get_translated_value
from apps.core.models import TenantBaseModel


class AccountType(models.TextChoices):
    ASSET = "asset", "Actif"
    LIABILITY = "liability", "Passif"
    EQUITY = "equity", "Capitaux propres"
    REVENUE = "revenue", "Produit"
    EXPENSE = "expense", "Charge"
    TREASURY = "treasury", "Trésorerie"


class JournalType(models.TextChoices):
    SALES = "sales", "Ventes"
    PURCHASES = "purchases", "Achats"
    CASH = "cash", "Caisse"
    BANK = "bank", "Banque"
    GENERAL = "general", "Opérations diverses"


class Account(TenantBaseModel):
    """
    Un compte du plan comptable de la coopérative.

    Les comptes système (is_system=True) correspondent au Plan Comptable
    Marocain (PCM) chargé via la commande `load_pcm`. Ils ne peuvent pas
    être supprimés mais peuvent être complétés par des sous-comptes.
    """

    code = models.CharField(
        max_length=10,
        db_index=True,
        help_text="Code du compte PCM, ex: '5141'",
    )
    name = TranslatedField(
        help_text='Libellé bilingue, ex: {"fr": "Banque", "ar": "بنك"}',
    )
    account_type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        db_index=True,
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.PROTECT,
        help_text="Compte parent (hiérarchie PCM).",
    )
    is_system = models.BooleanField(
        default=False,
        help_text="Compte PCM protégé — non supprimable.",
    )

    class Meta:
        verbose_name = "Compte comptable"
        verbose_name_plural = "Comptes comptables"
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                fields=["cooperative", "code"],
                name="unique_account_code_per_cooperative",
            ),
        ]
        indexes = [
            models.Index(fields=["cooperative", "account_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {get_translated_value(self.name, 'fr')}"


class Journal(TenantBaseModel):
    """
    Journal comptable d'une coopérative.

    Chaque écriture est rattachée à un journal (ventes, achats, caisse, banque,
    opérations diverses). Les journaux système sont créés avec `load_pcm`.
    """

    code = models.CharField(max_length=10, db_index=True)
    name = TranslatedField()
    journal_type = models.CharField(
        max_length=20,
        choices=JournalType.choices,
        db_index=True,
    )

    class Meta:
        verbose_name = "Journal comptable"
        verbose_name_plural = "Journaux comptables"
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                fields=["cooperative", "code"],
                name="unique_journal_code_per_cooperative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {get_translated_value(self.name, 'fr')}"


class AccountingEntry(TenantBaseModel):
    """
    En-tête d'une écriture comptable.

    Une écriture passe par deux états :
    - Brouillon (is_posted=False) : modifiable, non comptabilisée.
    - Validée  (is_posted=True)  : verrouillée, apparaît dans le grand livre.

    La règle Σ débit == Σ crédit est vérifiée dans services.post_entry()
    avant le passage en statut validé.
    """

    journal = models.ForeignKey(
        Journal,
        on_delete=models.PROTECT,
        related_name="entries",
    )
    entry_number = models.CharField(
        max_length=30,
        editable=False,
        db_index=True,
        help_text="Numéro auto-généré, ex: JV-2024-00001",
    )
    entry_date = models.DateField(db_index=True)
    period = models.CharField(
        max_length=7,
        db_index=True,
        help_text="Période au format YYYY-MM, ex: '2024-01'",
    )
    description = models.TextField(blank=True)
    is_posted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True = écriture validée/comptabilisée.",
    )

    class Meta:
        verbose_name = "Écriture comptable"
        verbose_name_plural = "Écritures comptables"
        ordering = ["-entry_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["cooperative", "entry_number"],
                name="unique_entry_number_per_cooperative",
            ),
        ]
        indexes = [
            models.Index(fields=["cooperative", "period"]),
            models.Index(fields=["cooperative", "is_posted"]),
        ]

    def __str__(self) -> str:
        return f"{self.entry_number} ({self.entry_date})"

    @property
    def total_debit(self) -> Decimal:
        return sum((line.debit for line in self.lines.all()), Decimal("0"))

    @property
    def total_credit(self) -> Decimal:
        return sum((line.credit for line in self.lines.all()), Decimal("0"))

    @property
    def is_balanced(self) -> bool:
        """Vérifie l'équilibre débit = crédit (règle comptable fondamentale)."""
        return self.total_debit == self.total_credit


class AccountingEntryLine(TenantBaseModel):
    """
    Ligne débit ou crédit d'une écriture comptable.

    Contraintes :
    - debit >= 0 et credit >= 0
    - Une ligne ne peut pas avoir à la fois un débit ET un crédit non nuls.
    """

    entry = models.ForeignKey(
        AccountingEntry,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="entry_lines",
    )
    label = models.CharField(max_length=200, blank=True)
    debit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0"),
    )
    credit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0"),
    )

    class Meta:
        verbose_name = "Ligne d'écriture"
        verbose_name_plural = "Lignes d'écriture"
        ordering = ["created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(debit__gte=0),
                name="accounting_line_debit_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(credit__gte=0),
                name="accounting_line_credit_non_negative",
            ),
            models.CheckConstraint(
                condition=~(models.Q(debit__gt=0) & models.Q(credit__gt=0)),
                name="accounting_line_not_both_debit_and_credit",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.account.code} | D:{self.debit} C:{self.credit}"

    @property
    def amount(self) -> Decimal:
        """Montant signé : positif pour débit, négatif pour crédit."""
        return self.debit if self.debit > 0 else -self.credit
