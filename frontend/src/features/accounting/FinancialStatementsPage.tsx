import { Printer, TrendingUp, TrendingDown, CheckCircle2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "../../shared/ui/Button";
import { AccountingSubNav } from "./AccountingSubNav";
import { getFinancialStatements } from "./api";
import type { FinancialStatementsResponse } from "./types";

function formatMoney(value: string | number): string {
  const num = typeof value === "number" ? value : Number(value) || 0;
  return `${num.toLocaleString("fr-MA", { minimumFractionDigits: 2 })} MAD`;
}

function accountLabel(name: string | { fr: string; ar?: string }): string {
  return typeof name === "string" ? name : name.fr;
}

export function FinancialStatementsPage() {
  const { t } = useTranslation();
  const [period, setPeriod] = useState("");
  const [activeTab, setActiveTab] = useState<"cpc" | "bilan">("cpc");
  const [data, setData] = useState<FinancialStatementsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setIsLoading(true);
    setError("");
    getFinancialStatements({ period: period || undefined })
      .then(setData)
      .catch(() => setError("Impossible de charger les états financiers."))
      .finally(() => setIsLoading(false));
  }, [period]);

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="page-title">États Financiers</h1>
          <p className="page-heading-subtitle">
            Compte de Produits et Charges (CPC) & Bilan condensé de la coopérative
          </p>
        </div>
        {data && (
          <Button variant="secondary" onClick={() => window.print()}>
            <Printer className="h-4 w-4" />
            Imprimer l'état financier
          </Button>
        )}
      </div>

      {/* Sous-navigation unifiée */}
      <AccountingSubNav />

      {/* Barre d'outils et filtres */}
      <div className="flex flex-wrap items-center justify-between gap-4 print:hidden">
        {/* Choix de l'état */}
        <div className="flex rounded-lg border border-ink-900/10 bg-sand-100 p-1">
          <button
            onClick={() => setActiveTab("cpc")}
            className={`rounded-md px-4 py-1.5 text-xs font-bold transition ${
              activeTab === "cpc"
                ? "bg-white text-ink-900 shadow-card"
                : "text-ink-700/70 hover:text-ink-900"
            }`}
          >
            Compte de Produits et Charges (CPC)
          </button>
          <button
            onClick={() => setActiveTab("bilan")}
            className={`rounded-md px-4 py-1.5 text-xs font-bold transition ${
              activeTab === "bilan"
                ? "bg-white text-ink-900 shadow-card"
                : "text-ink-700/70 hover:text-ink-900"
            }`}
          >
            Bilan Condensé
          </button>
        </div>

        {/* Filtre Période */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-ink-700">Période :</label>
          <input
            type="text"
            placeholder="ex: 2024-01"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="input-inline px-2.5 py-1.5 text-xs"
          />
        </div>
      </div>

      {error && (
        <div className="alert alert-error p-4">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="flex h-48 items-center justify-center text-sm text-ink-700">
          {t("common.loading")}
        </div>
      ) : data ? (
        <>
          {/* TAB 1: CPC */}
          {activeTab === "cpc" && (
            <div className="space-y-6">
              {/* Carte Résultat Net */}
              <div className={`card border-s-4 p-6 ${
                Number(data.cpc.net_result) >= 0 ? "border-sage-500" : "border-terracotta-500"
              }`}>
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <span className="font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">
                      Résultat Net de l'Exercice (CPC)
                    </span>
                    <p className={`mt-1 font-display text-3xl font-extrabold tracking-tight ${
                      Number(data.cpc.net_result) >= 0 ? "text-sage-800" : "text-terracotta-800"
                    }`}>
                      {formatMoney(data.cpc.net_result)}
                    </p>
                  </div>
                  <div className="flex items-center gap-6 text-sm">
                    <div>
                      <p className="text-xs text-ink-600">Total Produits (I)</p>
                      <p className="font-bold text-sage-700">{formatMoney(data.cpc.total_revenue)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-ink-600">Total Charges (II)</p>
                      <p className="font-bold text-terracotta-700">{formatMoney(data.cpc.total_expense)}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Tableaux Produits & Charges */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                {/* Section Produits */}
                <div className="card">
                  <div className="flex items-center justify-between border-b border-ink-900/5 bg-sage-50/50 px-5 py-3.5">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-sage-700" />
                      <h2 className="font-display text-sm font-bold text-sage-900">
                        I. Produits (Classe 7)
                      </h2>
                    </div>
                    <span className="font-mono text-xs font-bold text-sage-800">
                      {formatMoney(data.cpc.total_revenue)}
                    </span>
                  </div>

                  <table className="w-full text-start text-xs">
                    <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
                      <tr>
                        <th className="px-4 py-2.5 text-start">Code</th>
                        <th className="px-4 py-2.5 text-start">Libellé du compte</th>
                        <th className="px-4 py-2.5 text-end">Montant Net</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-ink-900/5">
                      {data.cpc.revenues.length === 0 ? (
                        <tr>
                          <td colSpan={3} className="px-4 py-6 text-center text-ink-700/50">
                            Aucun produit enregistré sur cette période.
                          </td>
                        </tr>
                      ) : (
                        data.cpc.revenues.map((item) => (
                          <tr key={item.account_code} className="hover:bg-sand-50">
                            <td className="px-4 py-2.5 font-mono font-semibold text-ink-900">
                              {item.account_code}
                            </td>
                            <td className="px-4 py-2.5 text-ink-800">{accountLabel(item.account_name)}</td>
                            <td className="px-4 py-2.5 text-end font-semibold text-sage-700">
                              {formatMoney(item.net_amount)}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Section Charges */}
                <div className="card">
                  <div className="flex items-center justify-between border-b border-ink-900/5 bg-terracotta-50/50 px-5 py-3.5">
                    <div className="flex items-center gap-2">
                      <TrendingDown className="h-4 w-4 text-terracotta-700" />
                      <h2 className="font-display text-sm font-bold text-terracotta-900">
                        II. Charges (Classe 6)
                      </h2>
                    </div>
                    <span className="font-mono text-xs font-bold text-terracotta-800">
                      {formatMoney(data.cpc.total_expense)}
                    </span>
                  </div>

                  <table className="w-full text-start text-xs">
                    <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
                      <tr>
                        <th className="px-4 py-2.5 text-start">Code</th>
                        <th className="px-4 py-2.5 text-start">Libellé du compte</th>
                        <th className="px-4 py-2.5 text-end">Montant Net</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-ink-900/5">
                      {data.cpc.expenses.length === 0 ? (
                        <tr>
                          <td colSpan={3} className="px-4 py-6 text-center text-ink-700/50">
                            Aucune charge enregistrée sur cette période.
                          </td>
                        </tr>
                      ) : (
                        data.cpc.expenses.map((item) => (
                          <tr key={item.account_code} className="hover:bg-sand-50">
                            <td className="px-4 py-2.5 font-mono font-semibold text-ink-900">
                              {item.account_code}
                            </td>
                            <td className="px-4 py-2.5 text-ink-800">{accountLabel(item.account_name)}</td>
                            <td className="px-4 py-2.5 text-end font-semibold text-terracotta-700">
                              {formatMoney(item.net_amount)}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: BILAN */}
          {activeTab === "bilan" && (
            <div className="space-y-6">
              {/* Carte Équilibre du Bilan */}
              <div className="card border-s-4 border-indigo-500 p-6">
                <div>
                  <span className="font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">
                    Bilan Condensé de la Coopérative
                  </span>
                  <div className="mt-1 flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-indigo-700" />
                    <span className="font-display text-lg font-bold tracking-tight text-ink-900">
                      Équilibre Bilan : Actif = Passif + Capitaux Propres
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-6 text-sm">
                  <div>
                    <p className="text-xs text-ink-600">Total Actif</p>
                    <p className="font-bold text-indigo-700">{formatMoney(data.bilan.total_assets)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-ink-600">Total Passif & Capitaux</p>
                    <p className="font-bold text-indigo-700">{formatMoney(data.bilan.total_passif_and_equity)}</p>
                  </div>
                </div>
              </div>

              {/* Tableaux Actif vs Passif */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                {/* ACTIF */}
                <div className="card">
                  <div className="flex items-center justify-between border-b border-ink-900/5 bg-indigo-50/50 px-5 py-3.5">
                    <h2 className="font-display text-sm font-bold text-indigo-900">
                      ACTIF (Immobilisations, Créances, Trésorerie)
                    </h2>
                    <span className="font-mono text-xs font-bold text-indigo-800">
                      {formatMoney(data.bilan.total_assets)}
                    </span>
                  </div>

                  <table className="w-full text-start text-xs">
                    <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
                      <tr>
                        <th className="px-4 py-2.5 text-start">Code</th>
                        <th className="px-4 py-2.5 text-start">Compte</th>
                        <th className="px-4 py-2.5 text-end">Solde Nette</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-ink-900/5">
                      {data.bilan.assets.length === 0 ? (
                        <tr>
                          <td colSpan={3} className="px-4 py-6 text-center text-ink-700/50">
                            Aucun élément d'actif enregistré.
                          </td>
                        </tr>
                      ) : (
                        data.bilan.assets.map((item) => (
                          <tr key={item.account_code} className="hover:bg-sand-50">
                            <td className="px-4 py-2.5 font-mono font-semibold text-ink-900">
                              {item.account_code}
                            </td>
                            <td className="px-4 py-2.5 text-ink-800">{accountLabel(item.account_name)}</td>
                            <td className="px-4 py-2.5 text-end font-semibold text-indigo-700">
                              {formatMoney(item.net_amount)}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                {/* PASSIF & CAPITAUX PROPRES */}
                <div className="card">
                  <div className="flex items-center justify-between border-b border-ink-900/5 bg-indigo-50/50 px-5 py-3.5">
                    <h2 className="font-display text-sm font-bold text-indigo-900">
                      PASSIF & CAPITAUX PROPRES
                    </h2>
                    <span className="font-mono text-xs font-bold text-indigo-800">
                      {formatMoney(data.bilan.total_passif_and_equity)}
                    </span>
                  </div>

                  <table className="w-full text-start text-xs">
                    <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
                      <tr>
                        <th className="px-4 py-2.5 text-start">Code</th>
                        <th className="px-4 py-2.5 text-start">Compte</th>
                        <th className="px-4 py-2.5 text-end">Solde Nette</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-ink-900/5">
                      {/* Capitaux et dettes */}
                      {[...data.bilan.equity, ...data.bilan.liabilities].length === 0 ? (
                        <tr>
                          <td colSpan={3} className="px-4 py-6 text-center text-ink-700/50">
                            Aucun élément de passif ou capitaux enregistré.
                          </td>
                        </tr>
                      ) : (
                        [...data.bilan.equity, ...data.bilan.liabilities].map((item) => (
                          <tr key={item.account_code} className="hover:bg-sand-50">
                            <td className="px-4 py-2.5 font-mono font-semibold text-ink-900">
                              {item.account_code}
                            </td>
                            <td className="px-4 py-2.5 text-ink-800">{accountLabel(item.account_name)}</td>
                            <td className="px-4 py-2.5 text-end font-semibold text-indigo-700">
                              {formatMoney(item.net_amount)}
                            </td>
                          </tr>
                        ))
                      )}
                      {/* Ligne Résultat de l'exercice */}
                      <tr className="bg-sand-100/60 font-semibold">
                        <td className="px-4 py-2.5 font-mono text-ink-900">119 / 1181</td>
                        <td className="px-4 py-2.5 text-ink-900">Résultat net de l'exercice</td>
                        <td className={`px-4 py-2.5 text-end ${
                          Number(data.cpc.net_result) >= 0 ? "text-sage-700" : "text-terracotta-700"
                        }`}>
                          {formatMoney(data.cpc.net_result)}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}
