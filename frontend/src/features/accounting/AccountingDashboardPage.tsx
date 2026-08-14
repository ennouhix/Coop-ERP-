import {
  TrendingUp,
  TrendingDown,
  Wallet,
  FileCheck,
  AlertCircle,
  Plus,
  ArrowRight,
  BookOpen,
  PieChart,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "../../shared/ui/Button";
import { AccountingSubNav } from "./AccountingSubNav";
import { getAccountingDashboard } from "./api";
import type { AccountingDashboardData } from "./types";

function formatMoney(value: string | number): string {
  const num = typeof value === "number" ? value : Number(value) || 0;
  return `${num.toLocaleString("fr-MA", { minimumFractionDigits: 2 })} MAD`;
}

export function AccountingDashboardPage() {
  const [data, setData] = useState<AccountingDashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setIsLoading(true);
    getAccountingDashboard()
      .then(setData)
      .catch(() => setError("Impossible de charger les données comptables."))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="page-title">Tableau de Bord Comptable</h1>
          <p className="page-heading-subtitle">
            Vue d'ensemble de la santé financière, trésorerie et écritures de la coopérative
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/accounting/entries/new">
            <Button>
              <Plus className="h-4 w-4" />
              Nouvelle écriture
            </Button>
          </Link>
        </div>
      </div>

      {/* Sous-navigation unifiée */}
      <AccountingSubNav />

      {error && (
        <div className="alert alert-error p-4">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="flex h-48 items-center justify-center text-sm text-ink-700">
          Chargement des indicateurs comptables...
        </div>
      ) : data ? (
        <>
          {/* Cartes KPI */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard
              label="Produits (Classe 7)"
              value={formatMoney(data.revenue_total)}
              icon={<TrendingUp className="h-5 w-5" />}
              accent="text-sage-600 bg-sage-50 border-sage-200"
              hint="Revenus d'exploitation comptabilisés"
            />
            <KpiCard
              label="Charges (Classe 6)"
              value={formatMoney(data.expense_total)}
              icon={<TrendingDown className="h-5 w-5" />}
              accent="text-terracotta-600 bg-terracotta-50 border-terracotta-200"
              hint="Dépenses et coûts de la période"
            />
            <KpiCard
              label="Résultat Net"
              value={formatMoney(data.net_result)}
              icon={<FileCheck className="h-5 w-5" />}
              accent={
                Number(data.net_result) >= 0
                  ? "text-moss-600 bg-moss-50 border-moss-200"
                  : "text-ochre-600 bg-ochre-50 border-ochre-200"
              }
              hint={Number(data.net_result) >= 0 ? "Bénéfice net enregistré" : "Déficit net enregistré"}
              valueClassName={Number(data.net_result) >= 0 ? "text-moss-800" : "text-ochre-800"}
            />
            <KpiCard
              label="Solde Trésorerie"
              value={formatMoney(data.treasury_balance)}
              icon={<Wallet className="h-5 w-5" />}
              accent="text-indigo-600 bg-indigo-50 border-indigo-200"
              hint="Comptes banques et caisses"
            />
          </div>

          {/* Alerte écritures en brouillon */}
          {data.draft_entries_count > 0 && (
            <div className="flex flex-wrap items-center justify-between gap-4 alert alert-warn p-4">
              <div className="flex items-center gap-3">
                <AlertCircle className="h-5 w-5 flex-shrink-0 text-ochre-600" />
                <div>
                  <p className="text-sm font-semibold">
                    {data.draft_entries_count} écriture(s) en brouillon en attente de validation
                  </p>
                  <p className="text-xs text-ochre-800/80">
                    Les écritures en brouillon ne sont pas encore intégrées dans le Grand Livre ni la Balance.
                  </p>
                </div>
              </div>
              <Link
                to="/accounting/entries"
                className="flex items-center gap-1.5 rounded-lg bg-ochre-600 px-3.5 py-1.5 text-xs font-semibold text-white transition hover:bg-ochre-700"
              >
                Examiner les brouillons
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          )}

          {/* Écritures récentes & Accès rapides */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {/* Tableau des écritures récentes */}
            <div className="card lg:col-span-2">
              <div className="card-header">
                <h2>
                  <span className="card-header-dot" />
                  Écritures Récentes
                </h2>
                <Link to="/accounting/entries" className="text-xs font-semibold text-moss-700 hover:underline">
                  Voir tout
                </Link>
              </div>

              {data.recent_entries.length === 0 ? (
                <p className="py-8 text-center text-xs text-ink-700/60">
                  Aucune écriture comptable enregistrée.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-start text-xs">
                    <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
                      <tr>
                        <th className="px-3 py-2.5 text-start">N° Écriture</th>
                        <th className="px-3 py-2.5 text-start">Date</th>
                        <th className="px-3 py-2.5 text-start">Journal</th>
                        <th className="px-3 py-2.5 text-end">Montant</th>
                        <th className="px-3 py-2.5 text-center">Statut</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-ink-900/5">
                      {data.recent_entries.map((entry) => (
                        <tr key={entry.id} className="hover:bg-sand-50">
                          <td className="px-3 py-2.5 font-mono font-semibold text-moss-700">
                            <Link to={`/accounting/entries/${entry.id}`} className="hover:underline">
                              {entry.entry_number}
                            </Link>
                          </td>
                          <td className="px-3 py-2.5 text-ink-700">{entry.entry_date}</td>
                          <td className="px-3 py-2.5 font-mono font-medium text-ink-900">
                            {entry.journal_code}
                          </td>
                          <td className="px-3 py-2.5 text-end font-semibold text-ink-900">
                            {formatMoney(entry.total_debit)}
                          </td>
                          <td className="px-3 py-2.5 text-center">
                            {entry.is_posted ? (
                              <span className="inline-block rounded-full bg-sage-100 px-2 py-0.5 text-[10px] font-semibold text-sage-700">
                                Validée
                              </span>
                            ) : (
                              <span className="inline-block rounded-full bg-ochre-100 px-2 py-0.5 text-[10px] font-semibold text-ochre-700">
                                Brouillon
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Actions rapides & Raccourcis */}
            <div className="space-y-4">
              <div className="card">
                <div className="card-header">
                  <h2>
                    <span className="card-header-dot" />
                    Raccourcis Comptables
                  </h2>
                </div>
                <div className="space-y-2 p-5">
                  <Link
                    to="/accounting/accounts"
                    className="flex items-center justify-between rounded-xl border border-ink-900/5 bg-sand-50/50 p-3 text-xs font-semibold text-ink-800 transition hover:bg-sand-100"
                  >
                    <div className="flex items-center gap-2.5">
                      <BookOpen className="h-4 w-4 text-moss-700" />
                      <span>Plan Comptable (PCM)</span>
                    </div>
                    <ArrowRight className="h-3.5 w-3.5 text-ink-700/40" />
                  </Link>

                  <Link
                    to="/accounting/ledger"
                    className="flex items-center justify-between rounded-xl border border-ink-900/5 bg-sand-50/50 p-3 text-xs font-semibold text-ink-800 transition hover:bg-sand-100"
                  >
                    <div className="flex items-center gap-2.5">
                      <BookOpen className="h-4 w-4 text-indigo-700" />
                      <span>Grand Livre des Comptes</span>
                    </div>
                    <ArrowRight className="h-3.5 w-3.5 text-ink-700/40" />
                  </Link>

                  <Link
                    to="/accounting/trial-balance"
                    className="flex items-center justify-between rounded-xl border border-ink-900/5 bg-sand-50/50 p-3 text-xs font-semibold text-ink-800 transition hover:bg-sand-100"
                  >
                    <div className="flex items-center gap-2.5">
                      <FileCheck className="h-4 w-4 text-sage-700" />
                      <span>Balance des Comptes</span>
                    </div>
                    <ArrowRight className="h-3.5 w-3.5 text-ink-700/40" />
                  </Link>

                  <Link
                    to="/accounting/statements"
                    className="flex items-center justify-between rounded-xl border border-ink-900/5 bg-sand-50/50 p-3 text-xs font-semibold text-ink-800 transition hover:bg-sand-100"
                  >
                    <div className="flex items-center gap-2.5">
                      <PieChart className="h-4 w-4 text-aubergine-700" />
                      <span>Compte de Produits & Charges (CPC)</span>
                    </div>
                    <ArrowRight className="h-3.5 w-3.5 text-ink-700/40" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}

function KpiCard({
  label,
  value,
  icon,
  accent,
  hint,
  valueClassName = "text-ink-900",
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  accent: string;
  hint: string;
  valueClassName?: string;
}) {
  return (
    <div className="card p-5 transition-shadow hover:shadow-lift">
      <div className="flex items-start justify-between">
        <p className="pt-0.5 font-mono text-[10px] font-medium uppercase tracking-eyebrow text-ink-600">{label}</p>
        <div className={`flex h-9 w-9 items-center justify-center rounded-md border ${accent}`}>{icon}</div>
      </div>
      <p className={`mt-3 font-display text-2xl font-extrabold tracking-tight ${valueClassName}`}>{value}</p>
      <p className="mt-1 text-xs text-ink-600">{hint}</p>
    </div>
  );
}
