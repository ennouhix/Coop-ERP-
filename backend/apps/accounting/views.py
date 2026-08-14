"""
Vues du module Comptabilité / Trésorerie.

Endpoints :
  GET/POST  /api/v1/accounting/accounts/             -> plan comptable
  GET       /api/v1/accounting/journals/             -> journaux
  GET/POST  /api/v1/accounting/entries/              -> liste / création écritures
  GET       /api/v1/accounting/entries/{id}/         -> détail écriture
  POST      /api/v1/accounting/entries/{id}/post/    -> valider l'écriture
  GET       /api/v1/accounting/ledger/               -> grand livre
  GET       /api/v1/accounting/trial-balance/        -> balance des comptes
"""
from __future__ import annotations

from decimal import Decimal

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounting import services
from apps.accounting.filters import AccountingEntryFilter
from apps.accounting.models import Account, AccountingEntry, Journal
from apps.accounting.serializers import (
    AccountingDashboardSerializer,
    AccountingEntryCreateSerializer,
    AccountingEntrySerializer,
    AccountSerializer,
    FinancialStatementsSerializer,
    GeneralLedgerRowSerializer,
    JournalSerializer,
    TrialBalanceRowSerializer,
)
from apps.authentication.permissions import IsCooperativeMember
from apps.roles_permissions.permissions import RequirePermission


# ---- Plan comptable ----

class AccountListCreateView(generics.ListCreateAPIView):
    """GET : liste du plan comptable  |  POST : créer un sous-compte personnalisé."""

    serializer_class = AccountSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["account_type"]
    search_fields = ["code", "name"]
    ordering_fields = ["code"]

    def get_queryset(self):  # noqa: ANN201
        return Account.objects.select_related("parent").all()

    def get_permissions(self):  # noqa: ANN201
        base = [IsAuthenticated(), IsCooperativeMember()]
        code = "accounting.edit" if self.request.method == "POST" else "accounting.view"
        base.append(RequirePermission(code)())
        return base

    def perform_create(self, serializer):  # noqa: ANN201
        serializer.save(cooperative=self.request.user.cooperative, created_by=self.request.user)


# ---- Journaux ----

class JournalListView(generics.ListAPIView):
    """GET : liste des journaux comptables."""

    serializer_class = JournalSerializer
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("accounting.view")]

    def get_queryset(self):  # noqa: ANN201
        return Journal.objects.all()


# ---- Écritures comptables ----

class AccountingEntryListCreateView(generics.ListCreateAPIView):
    """GET : liste des écritures  |  POST : créer une écriture en brouillon."""

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = AccountingEntryFilter
    ordering_fields = ["entry_date", "entry_number", "created_at"]

    def get_queryset(self):  # noqa: ANN201
        return (
            AccountingEntry.objects
            .select_related("journal")
            .prefetch_related("lines__account")
            .all()
        )

    def get_permissions(self):  # noqa: ANN201
        base = [IsAuthenticated(), IsCooperativeMember()]
        code = "accounting.edit" if self.request.method == "POST" else "accounting.view"
        base.append(RequirePermission(code)())
        return base

    def get_serializer_class(self):  # noqa: ANN201
        return AccountingEntryCreateSerializer if self.request.method == "POST" else AccountingEntrySerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = AccountingEntryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        cooperative_id = request.user.cooperative_id

        journal = get_object_or_404(Journal, pk=data["journal_id"], cooperative_id=cooperative_id)

        resolved_lines = []
        for line in data["lines"]:
            account = get_object_or_404(Account, pk=line["account_id"], cooperative_id=cooperative_id)
            resolved_lines.append({
                "account": account,
                "label": line.get("label", ""),
                "debit": line.get("debit", Decimal("0")),
                "credit": line.get("credit", Decimal("0")),
            })

        try:
            entry = services.create_accounting_entry(
                cooperative=request.user.cooperative,
                journal=journal,
                entry_date=data["entry_date"],
                description=data.get("description", ""),
                lines_data=resolved_lines,
                actor=request.user,
            )
        except services.AccountingError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AccountingEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


class AccountingEntryDetailView(generics.RetrieveAPIView):
    serializer_class = AccountingEntrySerializer
    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("accounting.view")]

    def get_queryset(self):  # noqa: ANN201
        return (
            AccountingEntry.objects
            .select_related("journal")
            .prefetch_related("lines__account")
            .all()
        )


class AccountingEntryPostView(APIView):
    """POST : valide (comptabilise) une écriture en brouillon."""

    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("accounting.post")]

    def post(self, request: Request, entry_id: str) -> Response:
        entry = get_object_or_404(
            AccountingEntry.objects.prefetch_related("lines"),
            pk=entry_id,
            cooperative_id=request.user.cooperative_id,
        )
        try:
            services.post_entry(entry=entry, actor=request.user)
        except services.AccountingError as exc:
            return Response({"error": {"message": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)
        entry.refresh_from_db()
        return Response(AccountingEntrySerializer(entry).data, status=status.HTTP_200_OK)


# ---- Grand livre ----

class GeneralLedgerView(APIView):
    """
    GET /api/v1/accounting/ledger/?account_id=<uuid>&date_from=YYYY-MM-DD&date_to=YYYY-MM-DD

    Retourne les mouvements d'un compte avec solde progressif.
    """

    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("accounting.view")]

    def get(self, request: Request) -> Response:
        account_id = request.query_params.get("account_id")
        if not account_id:
            return Response(
                {"error": {"message": "Le paramètre account_id est requis."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        account = get_object_or_404(Account, pk=account_id, cooperative_id=request.user.cooperative_id)

        date_from_str = request.query_params.get("date_from")
        date_to_str = request.query_params.get("date_to")

        from datetime import date as dt_date
        date_from = None
        date_to = None
        if date_from_str:
            try:
                date_from = dt_date.fromisoformat(date_from_str)
            except ValueError:
                return Response({"error": {"message": "Format date_from invalide (YYYY-MM-DD)."}}, status=400)
        if date_to_str:
            try:
                date_to = dt_date.fromisoformat(date_to_str)
            except ValueError:
                return Response({"error": {"message": "Format date_to invalide (YYYY-MM-DD)."}}, status=400)

        rows = services.get_general_ledger(account=account, date_from=date_from, date_to=date_to)

        return Response({
            "account": AccountSerializer(account).data,
            "rows": GeneralLedgerRowSerializer(rows, many=True).data,
        })


# ---- Balance des comptes ----

class TrialBalanceView(APIView):
    """
    GET /api/v1/accounting/trial-balance/?period=YYYY-MM

    Retourne la balance des comptes (une ligne par compte avec mouvements).
    """

    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("accounting.view")]

    def get(self, request: Request) -> Response:
        period = request.query_params.get("period") or None
        rows = services.get_trial_balance(
            cooperative=request.user.cooperative,
            period=period,
        )

        total_debit = sum((r["debit_total"] for r in rows), Decimal("0"))
        total_credit = sum((r["credit_total"] for r in rows), Decimal("0"))

        return Response({
            "period": period,
            "rows": TrialBalanceRowSerializer(rows, many=True).data,
            "total_debit": str(total_debit),
            "total_credit": str(total_credit),
        })


# ---- Tableau de bord comptable ----

class AccountingDashboardView(APIView):
    """
    GET /api/v1/accounting/dashboard/

    Retourne les KPIs du tableau de bord comptable et les écritures récentes.
    """

    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("accounting.view")]

    def get(self, request: Request) -> Response:
        kpis = services.get_accounting_dashboard_kpis(cooperative=request.user.cooperative)
        return Response(AccountingDashboardSerializer(kpis).data)


# ---- États financiers (CPC & Bilan) ----

class FinancialStatementsView(APIView):
    """
    GET /api/v1/accounting/financial-statements/?period=YYYY-MM

    Retourne le Compte de Produits et Charges (CPC) et le Bilan.
    """

    permission_classes = [IsAuthenticated, IsCooperativeMember, RequirePermission("accounting.view")]

    def get(self, request: Request) -> Response:
        period = request.query_params.get("period") or None
        statements = services.get_financial_statements(
            cooperative=request.user.cooperative,
            period=period,
        )
        return Response(FinancialStatementsSerializer(statements).data)

