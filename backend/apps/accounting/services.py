"""
Logique métier du module Comptabilité / Trésorerie.

Fonctions principales :
- create_accounting_entry() : crée une écriture en brouillon
- post_entry()              : valide l'écriture (Σ débit == Σ crédit obligatoire)
- get_general_ledger()      : grand livre d'un compte (solde progressif)
- get_trial_balance()       : balance des comptes (agrégation SQL)

Règle fondamentale : post_entry() lève AccountingError si l'écriture n'est
pas équilibrée — jamais de comptabilisation sans équilibre.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.db.models import Sum

from apps.accounting.models import (
    Account,
    AccountingEntry,
    AccountingEntryLine,
    AccountType,
    Journal,
)
from apps.audit.services import log_activity
from apps.cooperatives.models import Cooperative

ENTRY_NUMBER_PADDING = 5


class AccountingError(Exception):
    """Erreur métier comptable — message affiché directement à l'utilisateur."""


# ---- Génération du numéro d'écriture ----

@transaction.atomic
def _generate_entry_number(cooperative: Cooperative, journal: Journal) -> str:
    """
    Génère un numéro unique par journal et par année civile.
    Format : "{code journal}-{AAAA}-{NNNNN}" — ex: JV-2024-00001

    select_for_update() sur la coopérative garantit l'unicité en concurrent.
    """
    from apps.cooperatives.models import Cooperative as Coop  # éviter import circulaire
    Coop.objects.select_for_update().get(pk=cooperative.pk)

    current_year = date.today().year
    prefix = f"{journal.code}-{current_year}-"

    last = (
        AccountingEntry.all_objects
        .filter(cooperative=cooperative, journal=journal, entry_number__startswith=prefix)
        .order_by("-entry_number")
        .first()
    )
    if last is None:
        next_seq = 1
    else:
        try:
            next_seq = int(last.entry_number.split("-")[-1]) + 1
        except ValueError:
            next_seq = AccountingEntry.all_objects.filter(
                cooperative=cooperative, journal=journal,
            ).count() + 1

    return f"{prefix}{str(next_seq).zfill(ENTRY_NUMBER_PADDING)}"


# ---- Création d'une écriture ----

@transaction.atomic
def create_accounting_entry(
    *,
    cooperative: Cooperative,
    journal: Journal,
    entry_date: date,
    description: str = "",
    lines_data: list[dict],
    actor,  # noqa: ANN001
) -> AccountingEntry:
    """
    Crée une écriture comptable en brouillon (is_posted=False).

    lines_data : liste de dicts {account, label, debit, credit}.
    L'équilibre N'EST PAS vérifié ici — la validation se fait dans post_entry().
    """
    if len(lines_data) < 2:
        raise AccountingError("Une écriture doit contenir au moins deux lignes.")

    period = entry_date.strftime("%Y-%m")
    entry_number = _generate_entry_number(cooperative, journal)

    entry = AccountingEntry.objects.create(
        cooperative=cooperative,
        journal=journal,
        entry_number=entry_number,
        entry_date=entry_date,
        period=period,
        description=description,
        is_posted=False,
        created_by=actor,
    )

    for line in lines_data:
        AccountingEntryLine.objects.create(
            cooperative=cooperative,
            entry=entry,
            account=line["account"],
            label=line.get("label", ""),
            debit=line.get("debit", Decimal("0")),
            credit=line.get("credit", Decimal("0")),
            created_by=actor,
        )

    log_activity(
        cooperative=cooperative,
        actor=actor,
        action="accounting_entry.created",
        target_type="AccountingEntry",
        target_id=entry.id,
        target_repr=entry.entry_number,
    )
    return entry


# ---- Validation d'une écriture ----

@transaction.atomic
def post_entry(*, entry: AccountingEntry, actor) -> AccountingEntry:  # noqa: ANN001
    """
    Valide (comptabilise) une écriture : is_posted passe à True.

    Lève AccountingError si :
    - L'écriture est déjà validée.
    - Les totaux débit et crédit ne sont pas égaux (écriture non équilibrée).
    """
    if entry.is_posted:
        raise AccountingError("Cette écriture est déjà validée.")

    total_debit = sum((line.debit for line in entry.lines.all()), Decimal("0"))
    total_credit = sum((line.credit for line in entry.lines.all()), Decimal("0"))

    if total_debit != total_credit:
        diff = abs(total_debit - total_credit)
        raise AccountingError(
            f"L'écriture n'est pas équilibrée : débit {total_debit} ≠ crédit {total_credit} "
            f"(écart : {diff})."
        )

    entry.is_posted = True
    entry.updated_by = actor
    entry.save(update_fields=["is_posted", "updated_by", "updated_at"])

    log_activity(
        cooperative=entry.cooperative,
        actor=actor,
        action="accounting_entry.posted",
        target_type="AccountingEntry",
        target_id=entry.id,
        target_repr=entry.entry_number,
    )
    return entry


# ---- Grand livre ----

def get_general_ledger(
    *,
    account: Account,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> list[dict]:
    """
    Retourne les mouvements d'un compte (écriture validées uniquement)
    avec solde progressif cumulé, triés par date ASC.

    Le sens du solde dépend du type de compte :
    - Actif / Charge / Trésorerie : débit augmente le solde
    - Passif / Capitaux propres / Produit : crédit augmente le solde
    """
    qs = (
        AccountingEntryLine.objects
        .filter(account=account, entry__is_posted=True)
        .select_related("entry", "entry__journal")
        .order_by("entry__entry_date", "entry__created_at")
    )
    if date_from:
        qs = qs.filter(entry__entry_date__gte=date_from)
    if date_to:
        qs = qs.filter(entry__entry_date__lte=date_to)

    debit_types = {AccountType.ASSET, AccountType.EXPENSE, AccountType.TREASURY}
    running_balance = Decimal("0")
    rows = []

    for line in qs:
        if account.account_type in debit_types:
            running_balance += line.debit - line.credit
        else:
            running_balance += line.credit - line.debit

        rows.append({
            "entry_number": line.entry.entry_number,
            "entry_date": line.entry.entry_date,
            "journal_code": line.entry.journal.code,
            "description": line.label or line.entry.description,
            "debit": line.debit,
            "credit": line.credit,
            "running_balance": running_balance,
        })

    return rows


# ---- Balance des comptes ----

def get_trial_balance(
    *,
    cooperative: Cooperative,
    period: Optional[str] = None,
) -> list[dict]:
    """
    Retourne une ligne par compte ayant des mouvements (écritures validées).
    Chaque ligne contient : débit total, crédit total, solde débiteur, solde créditeur.

    Filtre optionnel par période (format YYYY-MM).
    """
    qs = AccountingEntryLine.objects.filter(
        cooperative=cooperative,
        entry__is_posted=True,
    )
    if period:
        qs = qs.filter(entry__period=period)

    aggregated = (
        qs.values("account__code", "account__name", "account__account_type")
        .annotate(
            debit_total=Sum("debit"),
            credit_total=Sum("credit"),
        )
        .order_by("account__code")
    )

    rows = []
    for row in aggregated:
        debit_total = row["debit_total"] or Decimal("0")
        credit_total = row["credit_total"] or Decimal("0")
        diff = debit_total - credit_total
        rows.append({
            "account_code": row["account__code"],
            "account_name": row["account__name"],
            "debit_total": debit_total,
            "credit_total": credit_total,
            "debit_balance": max(Decimal("0"), diff),
            "credit_balance": max(Decimal("0"), -diff),
        })

    return rows


# ---- Tableau de bord comptable ----

def get_accounting_dashboard_kpis(*, cooperative: Cooperative) -> dict:
    """
    Calcule les indicateurs clés (KPIs) comptables pour la coopérative :
    - Total Produits (Classe 7)
    - Total Charges (Classe 6)
    - Résultat Net (Produits - Charges)
    - Solde Trésorerie (Comptes de Trésorerie)
    - Écritures en brouillon et validées
    - Liste des 5 dernières écritures
    """
    posted_lines = AccountingEntryLine.objects.filter(
        cooperative=cooperative,
        entry__is_posted=True,
    ).select_related("account")

    revenue_total = Decimal("0")
    expense_total = Decimal("0")
    treasury_balance = Decimal("0")

    for line in posted_lines:
        acc_type = line.account.account_type
        if acc_type == AccountType.REVENUE:
            revenue_total += line.credit - line.debit
        elif acc_type == AccountType.EXPENSE:
            expense_total += line.debit - line.credit
        elif acc_type == AccountType.TREASURY:
            treasury_balance += line.debit - line.credit

    net_result = revenue_total - expense_total

    entries_qs = AccountingEntry.objects.filter(cooperative=cooperative)
    draft_entries_count = entries_qs.filter(is_posted=False).count()
    posted_entries_count = entries_qs.filter(is_posted=True).count()

    recent_entries = list(
        entries_qs.select_related("journal")
        .order_by("-entry_date", "-created_at")[:5]
    )

    return {
        "revenue_total": revenue_total,
        "expense_total": expense_total,
        "net_result": net_result,
        "treasury_balance": treasury_balance,
        "draft_entries_count": draft_entries_count,
        "posted_entries_count": posted_entries_count,
        "recent_entries": recent_entries,
    }


# ---- États financiers (CPC & Bilan) ----

def get_financial_statements(
    *,
    cooperative: Cooperative,
    period: Optional[str] = None,
) -> dict:
    """
    Retourne le Compte de Produits et Charges (CPC) et le Bilan condensé.
    """
    qs = AccountingEntryLine.objects.filter(
        cooperative=cooperative,
        entry__is_posted=True,
    )
    if period:
        qs = qs.filter(entry__period=period)

    aggregated = (
        qs.values("account__code", "account__name", "account__account_type")
        .annotate(
            debit_total=Sum("debit"),
            credit_total=Sum("credit"),
        )
        .order_by("account__code")
    )

    revenues = []
    expenses = []
    assets = []
    liabilities = []
    equity = []

    total_revenue = Decimal("0")
    total_expense = Decimal("0")
    total_assets = Decimal("0")
    total_liabilities = Decimal("0")
    total_equity = Decimal("0")

    for row in aggregated:
        debit = row["debit_total"] or Decimal("0")
        credit = row["credit_total"] or Decimal("0")
        acc_type = row["account__account_type"]
        item = {
            "account_code": row["account__code"],
            "account_name": row["account__name"],
            "debit": debit,
            "credit": credit,
        }

        if acc_type == AccountType.REVENUE:
            net = credit - debit
            item["net_amount"] = net
            revenues.append(item)
            total_revenue += net
        elif acc_type == AccountType.EXPENSE:
            net = debit - credit
            item["net_amount"] = net
            expenses.append(item)
            total_expense += net
        elif acc_type in (AccountType.ASSET, AccountType.TREASURY):
            net = debit - credit
            item["net_amount"] = net
            assets.append(item)
            total_assets += net
        elif acc_type == AccountType.LIABILITY:
            net = credit - debit
            item["net_amount"] = net
            liabilities.append(item)
            total_liabilities += net
        elif acc_type == AccountType.EQUITY:
            net = credit - debit
            item["net_amount"] = net
            equity.append(item)
            total_equity += net

    net_result = total_revenue - total_expense

    return {
        "period": period,
        "cpc": {
            "revenues": revenues,
            "expenses": expenses,
            "total_revenue": total_revenue,
            "total_expense": total_expense,
            "net_result": net_result,
        },
        "bilan": {
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "total_equity": total_equity,
            "total_passif_and_equity": total_liabilities + total_equity + net_result,
        },
    }

