import { CheckCircle2, Printer, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Button } from "../../shared/ui/Button";
import { getTrialBalance } from "./api";
import type { TrialBalanceRow } from "./types";

function formatMoney(value: string): string {
  return `${Number(value).toLocaleString("fr-MA", { minimumFractionDigits: 2 })} MAD`;
}

import { AccountingSubNav } from "./AccountingSubNav";

function accountLabel(name: string | { fr: string; ar: string }): string {
  return typeof name === "string" ? name : name.fr;
}

export function TrialBalancePage() {
  const { t } = useTranslation();
  const [period, setPeriod] = useState("");
  const [rows, setRows] = useState<TrialBalanceRow[]>([]);
  const [totalDebit, setTotalDebit] = useState("0");
  const [totalCredit, setTotalCredit] = useState("0");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setIsLoading(true);
    setError("");
    getTrialBalance({ period: period || undefined })
      .then((data) => {
        setRows(data.rows);
        setTotalDebit(data.total_debit);
        setTotalCredit(data.total_credit);
      })
      .catch(() => setError("Impossible de charger la balance des comptes."))
      .finally(() => setIsLoading(false));
  }, [period]);

  const isBalanced = Number(totalDebit) === Number(totalCredit);

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Balance des Comptes</h1>
          <p className="page-heading-subtitle">
            Synthèse des mouvements et soldes par compte (écritures validées)
          </p>
        </div>
        {rows.length > 0 && (
          <Button variant="secondary" onClick={() => window.print()}>
            <Printer className="h-4 w-4" />
            Imprimer
          </Button>
        )}
      </div>

      {/* Sous-navigation unifiée */}
      <AccountingSubNav />

      {/* Filtre période + statut d'équilibre */}
      <div className="mt-6 flex flex-wrap items-end justify-between gap-3 print:hidden">
        <div>
          <label className="mb-1 block text-xs font-medium text-ink-700/70">Période</label>
          <input
            type="text"
            placeholder="ex: 2024-01"
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="input-inline"
          />
          <p className="mt-1 text-xs text-ink-700/50">Laisser vide pour toutes les périodes.</p>
        </div>
        {!isLoading && rows.length > 0 && (
          <div
            className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium ${
              isBalanced ? "bg-sage-100 text-sage-700" : "bg-terracotta-100 text-terracotta-700"
            }`}
          >
            {isBalanced ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
            {isBalanced ? "Balance équilibrée" : "Balance déséquilibrée"}
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 alert alert-error">
          {error}
        </div>
      )}

      {/* Tableau */}
      <div className="mt-4 card">
        <table className="w-full text-start text-sm">
          <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
            <tr>
              <th className="px-4 py-3 text-start">Code</th>
              <th className="px-4 py-3 text-start">Compte</th>
              <th className="px-4 py-3 text-end">Total débit</th>
              <th className="px-4 py-3 text-end">Total crédit</th>
              <th className="px-4 py-3 text-end">Solde débiteur</th>
              <th className="px-4 py-3 text-end">Solde créditeur</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-900/5">
            {isLoading && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-ink-700">
                  {t("common.loading")}
                </td>
              </tr>
            )}
            {!isLoading && rows.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-ink-700">
                  Aucun mouvement validé pour cette période.
                </td>
              </tr>
            )}
            {!isLoading && rows.map((row) => (
              <tr key={row.account_code} className="hover:bg-sand-50">
                <td className="px-4 py-3 font-mono text-xs font-semibold text-ink-900">{row.account_code}</td>
                <td className="px-4 py-3 text-ink-700">{accountLabel(row.account_name)}</td>
                <td className="px-4 py-3 text-end text-ink-900">{formatMoney(row.debit_total)}</td>
                <td className="px-4 py-3 text-end text-ink-900">{formatMoney(row.credit_total)}</td>
                <td className="px-4 py-3 text-end font-medium text-sage-700">
                  {Number(row.debit_balance) > 0 ? formatMoney(row.debit_balance) : "—"}
                </td>
                <td className="px-4 py-3 text-end font-medium text-terracotta-600">
                  {Number(row.credit_balance) > 0 ? formatMoney(row.credit_balance) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
          {!isLoading && rows.length > 0 && (
            <tfoot className="border-t-2 border-ink-900/10 bg-sand-50">
              <tr>
                <td colSpan={2} className="px-4 py-3 text-end font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">
                  Totaux
                </td>
                <td className="px-4 py-3 text-end font-bold text-ink-900">{formatMoney(totalDebit)}</td>
                <td className="px-4 py-3 text-end font-bold text-ink-900">{formatMoney(totalCredit)}</td>
                <td colSpan={2} className="px-4 py-3 text-end text-xs font-medium text-ink-700/60">
                  {isBalanced ? "Σ débit = Σ crédit ✓" : "⚠ écart détecté"}
                </td>
              </tr>
            </tfoot>
          )}
        </table>
      </div>
    </div>
  );
}
