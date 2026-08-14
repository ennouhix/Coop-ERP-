from __future__ import annotations

from django.urls import path

from apps.accounting.views import (
    AccountingDashboardView,
    AccountingEntryDetailView,
    AccountingEntryListCreateView,
    AccountingEntryPostView,
    AccountListCreateView,
    FinancialStatementsView,
    GeneralLedgerView,
    JournalListView,
    TrialBalanceView,
)

app_name = "accounting"

urlpatterns = [
    path("dashboard/", AccountingDashboardView.as_view(), name="accounting-dashboard"),
    path("accounts/", AccountListCreateView.as_view(), name="account-list"),
    path("journals/", JournalListView.as_view(), name="journal-list"),
    path("entries/", AccountingEntryListCreateView.as_view(), name="entry-list"),
    path("entries/<uuid:pk>/", AccountingEntryDetailView.as_view(), name="entry-detail"),
    path("entries/<uuid:entry_id>/post/", AccountingEntryPostView.as_view(), name="entry-post"),
    path("ledger/", GeneralLedgerView.as_view(), name="general-ledger"),
    path("trial-balance/", TrialBalanceView.as_view(), name="trial-balance"),
    path("financial-statements/", FinancialStatementsView.as_view(), name="financial-statements"),
]
