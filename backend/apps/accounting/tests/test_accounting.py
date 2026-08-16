"""
Tests du module Comptabilité / Trésorerie.

Couvre :
1. Création d'écriture + numéro auto-généré
2. Validation d'une écriture équilibrée → succès
3. Validation d'une écriture non équilibrée → AccountingError
4. Double validation → AccountingError
5. Grand livre : solde progressif correct
6. Balance des comptes : Σ débit == Σ crédit
7. Isolation multi-tenant : coopérative A ne voit pas les données de B
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.accounting.models import (
    Account,
    AccountType,
    Journal,
    JournalType,
)
from apps.accounting.services import (
    AccountingError,
    create_accounting_entry,
    get_general_ledger,
    get_trial_balance,
    post_entry,
)


@pytest.fixture
def cooperative(db):
    from apps.cooperatives.models import Cooperative

    return Cooperative.objects.create(
        name="Coopérative Test",
        slug="coop-test",
        ice="123456789",
        is_active=True,
    )


@pytest.fixture
def cooperative_b(db):
    from apps.cooperatives.models import Cooperative

    return Cooperative.objects.create(
        name="Coopérative B",
        slug="coop-b",
        ice="987654321",
        is_active=True,
    )


@pytest.fixture
def user(db, cooperative):
    from apps.authentication.models import User

    return User.objects.create_user(
        username="test_accountant",
        email="test@example.com",
        password="testpass123",
        cooperative=cooperative,
    )


@pytest.fixture
def journal(db, cooperative):
    return Journal.all_objects.create(
        cooperative=cooperative,
        code="OD",
        name={"fr": "Opérations diverses", "ar": "عمليات متنوعة"},
        journal_type=JournalType.GENERAL,
    )


@pytest.fixture
def account_bank(db, cooperative):
    return Account.all_objects.create(
        cooperative=cooperative,
        code="5141",
        name={"fr": "Banque", "ar": "بنك"},
        account_type=AccountType.TREASURY,
    )


@pytest.fixture
def account_capital(db, cooperative):
    return Account.all_objects.create(
        cooperative=cooperative,
        code="101",
        name={"fr": "Capital social", "ar": "رأس المال"},
        account_type=AccountType.EQUITY,
    )


@pytest.fixture
def account_revenue(db, cooperative):
    return Account.all_objects.create(
        cooperative=cooperative,
        code="701",
        name={"fr": "Ventes", "ar": "المبيعات"},
        account_type=AccountType.REVENUE,
    )


# ---- Tests ----


@pytest.mark.django_db
def test_entry_number_auto_generated(cooperative, journal, account_bank, account_capital, user):
    """Le numéro d'écriture doit être auto-généré au format JV-AAAA-NNNNN."""
    entry = create_accounting_entry(
        cooperative=cooperative,
        journal=journal,
        entry_date=__import__("datetime").date(2024, 1, 15),
        description="Test",
        lines_data=[
            {"account": account_bank, "debit": Decimal("1000"), "credit": Decimal("0")},
            {"account": account_capital, "debit": Decimal("0"), "credit": Decimal("1000")},
        ],
        actor=user,
    )
    assert entry.entry_number.startswith("OD-2024-")
    assert not entry.is_posted


@pytest.mark.django_db
def test_balanced_entry_can_be_posted(cooperative, journal, account_bank, account_capital, user):
    """Une écriture équilibrée (Σ débit == Σ crédit) doit pouvoir être validée."""
    entry = create_accounting_entry(
        cooperative=cooperative,
        journal=journal,
        entry_date=__import__("datetime").date(2024, 1, 15),
        description="Apport en capital",
        lines_data=[
            {"account": account_bank, "debit": Decimal("5000"), "credit": Decimal("0")},
            {"account": account_capital, "debit": Decimal("0"), "credit": Decimal("5000")},
        ],
        actor=user,
    )
    result = post_entry(entry=entry, actor=user)
    assert result.is_posted is True


@pytest.mark.django_db
def test_unbalanced_entry_cannot_be_posted(
    cooperative, journal, account_bank, account_capital, user
):
    """Une écriture non équilibrée doit lever AccountingError à la validation."""
    entry = create_accounting_entry(
        cooperative=cooperative,
        journal=journal,
        entry_date=__import__("datetime").date(2024, 1, 15),
        description="Écriture non équilibrée",
        lines_data=[
            {"account": account_bank, "debit": Decimal("5000"), "credit": Decimal("0")},
            {"account": account_capital, "debit": Decimal("0"), "credit": Decimal("3000")},
        ],
        actor=user,
    )
    with pytest.raises(AccountingError, match="n'est pas équilibrée"):
        post_entry(entry=entry, actor=user)


@pytest.mark.django_db
def test_already_posted_entry_cannot_be_posted_again(
    cooperative, journal, account_bank, account_capital, user
):
    """Double validation d'une écriture doit lever AccountingError."""
    entry = create_accounting_entry(
        cooperative=cooperative,
        journal=journal,
        entry_date=__import__("datetime").date(2024, 1, 15),
        description="Test",
        lines_data=[
            {"account": account_bank, "debit": Decimal("1000"), "credit": Decimal("0")},
            {"account": account_capital, "debit": Decimal("0"), "credit": Decimal("1000")},
        ],
        actor=user,
    )
    post_entry(entry=entry, actor=user)
    with pytest.raises(AccountingError, match="déjà validée"):
        post_entry(entry=entry, actor=user)


@pytest.mark.django_db
def test_general_ledger_running_balance(
    cooperative, journal, account_bank, account_capital, account_revenue, user
):
    """Le solde progressif du grand livre doit s'accumuler correctement."""
    import datetime

    # Écriture 1 : apport banque 10000
    e1 = create_accounting_entry(
        cooperative=cooperative,
        journal=journal,
        entry_date=datetime.date(2024, 1, 1),
        description="Apport",
        lines_data=[
            {"account": account_bank, "debit": Decimal("10000"), "credit": Decimal("0")},
            {"account": account_capital, "debit": Decimal("0"), "credit": Decimal("10000")},
        ],
        actor=user,
    )
    post_entry(entry=e1, actor=user)

    # Écriture 2 : vente 2000
    e2 = create_accounting_entry(
        cooperative=cooperative,
        journal=journal,
        entry_date=datetime.date(2024, 1, 5),
        description="Vente",
        lines_data=[
            {"account": account_bank, "debit": Decimal("2000"), "credit": Decimal("0")},
            {"account": account_revenue, "debit": Decimal("0"), "credit": Decimal("2000")},
        ],
        actor=user,
    )
    post_entry(entry=e2, actor=user)

    rows = get_general_ledger(account=account_bank)
    assert len(rows) == 2
    # Compte de trésorerie (ASSET type) : débit augmente le solde
    assert rows[0]["running_balance"] == Decimal("10000")
    assert rows[1]["running_balance"] == Decimal("12000")


@pytest.mark.django_db
def test_trial_balance_sums_correctly(cooperative, journal, account_bank, account_capital, user):
    """La balance : Σ soldes débiteurs == Σ soldes créditeurs."""
    import datetime

    entry = create_accounting_entry(
        cooperative=cooperative,
        journal=journal,
        entry_date=datetime.date(2024, 2, 1),
        description="Test balance",
        lines_data=[
            {"account": account_bank, "debit": Decimal("8000"), "credit": Decimal("0")},
            {"account": account_capital, "debit": Decimal("0"), "credit": Decimal("8000")},
        ],
        actor=user,
    )
    post_entry(entry=entry, actor=user)

    rows = get_trial_balance(cooperative=cooperative)
    total_debit_balance = sum(r["debit_balance"] for r in rows)
    total_credit_balance = sum(r["credit_balance"] for r in rows)
    assert total_debit_balance == total_credit_balance


@pytest.mark.django_db
def test_tenant_isolation(cooperative, cooperative_b, journal, account_bank, account_capital, user):
    """Les écritures de la coopérative A ne doivent pas être visibles dans B."""
    import datetime

    entry = create_accounting_entry(
        cooperative=cooperative,
        journal=journal,
        entry_date=datetime.date(2024, 3, 1),
        description="Écriture A",
        lines_data=[
            {"account": account_bank, "debit": Decimal("500"), "credit": Decimal("0")},
            {"account": account_capital, "debit": Decimal("0"), "credit": Decimal("500")},
        ],
        actor=user,
    )
    post_entry(entry=entry, actor=user)

    rows_b = get_trial_balance(cooperative=cooperative_b)
    assert len(rows_b) == 0, "La coopérative B ne doit voir aucune écriture de A"


@pytest.mark.django_db
def test_entry_requires_at_least_two_lines(cooperative, journal, account_bank, user):
    """Une écriture avec une seule ligne doit être refusée."""
    import datetime

    with pytest.raises(AccountingError, match="au moins deux lignes"):
        create_accounting_entry(
            cooperative=cooperative,
            journal=journal,
            entry_date=datetime.date(2024, 1, 1),
            description="Ligne unique",
            lines_data=[
                {"account": account_bank, "debit": Decimal("1000"), "credit": Decimal("0")},
            ],
            actor=user,
        )


@pytest.mark.django_db
def test_accounting_dashboard_kpis(cooperative, journal, account_bank, account_revenue, user):
    """Vérification des calculs des KPIs du tableau de bord comptable."""
    import datetime

    from apps.accounting.services import get_accounting_dashboard_kpis

    # Écriture brouillon
    create_accounting_entry(
        cooperative=cooperative,
        journal=journal,
        entry_date=datetime.date(2024, 1, 1),
        description="Brouillon",
        lines_data=[
            {"account": account_bank, "debit": Decimal("100"), "credit": Decimal("0")},
            {"account": account_revenue, "debit": Decimal("0"), "credit": Decimal("100")},
        ],
        actor=user,
    )

    # Écriture validée
    entry2 = create_accounting_entry(
        cooperative=cooperative,
        journal=journal,
        entry_date=datetime.date(2024, 1, 2),
        description="Vente",
        lines_data=[
            {"account": account_bank, "debit": Decimal("1500"), "credit": Decimal("0")},
            {"account": account_revenue, "debit": Decimal("0"), "credit": Decimal("1500")},
        ],
        actor=user,
    )
    post_entry(entry=entry2, actor=user)

    kpis = get_accounting_dashboard_kpis(cooperative=cooperative)
    assert kpis["revenue_total"] == Decimal("1500")
    assert kpis["treasury_balance"] == Decimal("1500")
    assert kpis["draft_entries_count"] == 1
    assert kpis["posted_entries_count"] == 1


@pytest.mark.django_db
def test_financial_statements_cpc_and_bilan(
    cooperative, journal, account_bank, account_capital, account_revenue, user
):
    """Vérification des états financiers CPC et Bilan."""
    import datetime

    from apps.accounting.services import get_financial_statements

    entry = create_accounting_entry(
        cooperative=cooperative,
        journal=journal,
        entry_date=datetime.date(2024, 1, 10),
        description="Vente marchandise",
        lines_data=[
            {"account": account_bank, "debit": Decimal("3000"), "credit": Decimal("0")},
            {"account": account_revenue, "debit": Decimal("0"), "credit": Decimal("3000")},
        ],
        actor=user,
    )
    post_entry(entry=entry, actor=user)

    statements = get_financial_statements(cooperative=cooperative)
    assert statements["cpc"]["total_revenue"] == Decimal("3000")
    assert statements["cpc"]["net_result"] == Decimal("3000")
    assert statements["bilan"]["total_assets"] == Decimal("3000")


@pytest.mark.django_db
def test_accountant_role_has_accounting_permissions():
    """Le rôle ACCOUNTANT doit posséder les permissions accounting.view, edit et post."""
    from apps.authentication.models import UserRole
    from apps.roles_permissions.matrix import has_permission

    assert has_permission(UserRole.ACCOUNTANT, "accounting.view") is True
    assert has_permission(UserRole.ACCOUNTANT, "accounting.edit") is True
    assert has_permission(UserRole.ACCOUNTANT, "accounting.post") is True
