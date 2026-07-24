import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { AxiosError } from "axios";

import { apiClient } from "../../api/client";

interface DashboardSummary {
  period: { date_from: string; date_to: string };
  members: { active_count: number; total_count: number };
  partners: { active_customers: number; active_suppliers: number };
  sales: {
    orders_draft: number; orders_confirmed: number;
    orders_partially_delivered: number; orders_delivered: number;
    revenue_invoiced_period: string;
  };
  purchases: {
    orders_draft: number; orders_confirmed: number;
    orders_partially_received: number; orders_received: number;
    spend_confirmed_period: string;
  };
  stock: { total_stock_value: string; low_stock_lines_count: number };
  billing: { total_outstanding_balance: string; overdue_invoices_count: number; amount_collected_period: string };
}

function formatMAD(value: string): string {
  return `${Number(value).toLocaleString("fr-MA", { minimumFractionDigits: 2 })} MAD`;
}

function KpiCard({ label, value, tone = "default" }: { label: string; value: string; tone?: "default" | "warning" | "accent" }) {
  const toneClasses = {
    default: "text-ink-900",
    warning: "text-terracotta-600",
    accent: "text-moss-600",
  }[tone];

  return (
    <div className="rounded-lg border border-ink-900/5 bg-white p-5 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-ink-700/70">{label}</p>
      <p className={`mt-2 font-display text-2xl font-bold ${toneClasses}`}>{value}</p>
    </div>
  );
}

export function DashboardPage() {
  const { t } = useTranslation();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    apiClient
      .get<DashboardSummary>("/dashboard/summary/")
      .then((response) => {
        if (!cancelled) setSummary(response.data);
      })
      .catch((err: AxiosError) => {
        // Message générique côté UI (ne jamais exposer de détail technique
        // à l'utilisateur final), mais on logge le vrai statut/contenu en
        // console pour que le diagnostic ne dépende pas uniquement des logs
        // serveur — un développeur qui ouvre les devtools voit la cause
        // immédiatement (403 permission, 500 serveur, réseau...).
        console.error("Échec du chargement du dashboard :", err.response?.status, err.response?.data ?? err.message);
        if (!cancelled) setError(t("dashboard.error"));
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [t]);

  if (isLoading) {
    return <p className="text-sm text-ink-700">{t("common.loading")}</p>;
  }

  if (error || !summary) {
    return <p className="text-sm text-terracotta-600">{error ?? t("dashboard.error")}</p>;
  }

  return (
    <div>
      <h1 className="font-display text-2xl font-bold text-ink-900">{t("nav.dashboard")}</h1>
      <p className="mt-1 text-sm text-ink-700">
        {t("dashboard.period", { from: summary.period.date_from, to: summary.period.date_to })}
      </p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label={t("dashboard.revenue")} value={formatMAD(summary.sales.revenue_invoiced_period)} tone="accent" />
        <KpiCard label={t("dashboard.spend")} value={formatMAD(summary.purchases.spend_confirmed_period)} />
        <KpiCard label={t("dashboard.stock_value")} value={formatMAD(summary.stock.total_stock_value)} />
        <KpiCard
          label={t("dashboard.outstanding")}
          value={formatMAD(summary.billing.total_outstanding_balance)}
          tone={summary.billing.overdue_invoices_count > 0 ? "warning" : "default"}
        />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label={t("dashboard.active_members")} value={String(summary.members.active_count)} />
        <KpiCard label={t("dashboard.low_stock")} value={String(summary.stock.low_stock_lines_count)} tone={summary.stock.low_stock_lines_count > 0 ? "warning" : "default"} />
        <KpiCard label={t("dashboard.overdue_invoices")} value={String(summary.billing.overdue_invoices_count)} tone={summary.billing.overdue_invoices_count > 0 ? "warning" : "default"} />
        <KpiCard label={t("dashboard.orders_delivered")} value={String(summary.sales.orders_delivered)} />
      </div>
    </div>
  );
}
