import { Printer } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Button } from "../../shared/ui/Button";
import { getGeneralLedger, listAccounts } from "./api";
import type { Account, GeneralLedgerRow } from "./types";

import { AccountingSubNav } from "./AccountingSubNav";

function formatMoney(value: string): string {
  return `${Number(value).toLocaleString("fr-MA", { minimumFractionDigits: 2 })} MAD`;
}

export function GeneralLedgerPage() {
  const { t } = useTranslation();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [accountId, setAccountId] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [rows, setRows] = useState<GeneralLedgerRow[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    listAccounts().then(setAccounts);
  }, []);

  useEffect(() => {
    if (!accountId) {
      setRows([]);
      setSelectedAccount(null);
      setHasSearched(false);
      return;
    }
    setIsLoading(true);
    setError("");
    getGeneralLedger({
      account_id: accountId,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    })
      .then((data) => {
        setRows(data.rows);
        setSelectedAccount(data.account);
        setHasSearched(true);
      })
      .catch(() => setError("Impossible de charger le grand livre pour ce compte."))
      .finally(() => setIsLoading(false));
  }, [accountId, dateFrom, dateTo]);

  const totals = useMemo(() => {
    const totalDebit = rows.reduce((sum, r) => sum + Number(r.debit), 0);
    const totalCredit = rows.reduce((sum, r) => sum + Number(r.credit), 0);
    const closingBalance = rows.length > 0 ? Number(rows[rows.length - 1].running_balance) : 0;
    return { totalDebit, totalCredit, closingBalance };
  }, [rows]);

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Grand Livre</h1>
          <p className="page-heading-subtitle">
            Mouvements détaillés d'un compte avec solde progressif
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

      {/* Filtres */}
      <div className="mt-6 flex flex-wrap items-end gap-3 print:hidden">
        <div>
          <label className="mb-1 block text-xs font-medium text-ink-700/70">Compte</label>
          <select
            value={accountId}
            onChange={(e) => setAccountId(e.target.value)}
            className="min-w-[280px] input-inline"
          >
            <option value="">— Sélectionner un compte —</option>
            {accounts.map((a) => (
              <option key={a.id} value={a.id}>{a.code} — {a.name_display}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-ink-700/70">Du</label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="input-inline"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-ink-700/70">Au</label>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="input-inline"
          />
        </div>
      </div>

      {/* Fiche compte sélectionné */}
      {selectedAccount && (
        <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="card p-4">
            <p className="font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">Compte</p>
            <p className="mt-1 text-sm font-semibold text-ink-900">
              {selectedAccount.code} — {selectedAccount.name_display}
            </p>
          </div>
          <div className="card p-4">
            <p className="font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">Total débit</p>
            <p className="mt-1 text-sm font-semibold text-ink-900">
              {formatMoney(totals.totalDebit.toFixed(2))}
            </p>
          </div>
          <div className="card p-4">
            <p className="font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">Total crédit</p>
            <p className="mt-1 text-sm font-semibold text-ink-900">
              {formatMoney(totals.totalCredit.toFixed(2))}
            </p>
          </div>
          <div className="card p-4">
            <p className="font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">Solde de clôture</p>
            <p className={`mt-1 text-sm font-semibold ${totals.closingBalance >= 0 ? "text-sage-700" : "text-terracotta-600"}`}>
              {formatMoney(totals.closingBalance.toFixed(2))}
            </p>
          </div>
        </div>
      )}

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
              <th className="px-4 py-3 text-start">Date</th>
              <th className="px-4 py-3 text-start">N° Écriture</th>
              <th className="px-4 py-3 text-start">Journal</th>
              <th className="px-4 py-3 text-start">Libellé</th>
              <th className="px-4 py-3 text-end">Débit</th>
              <th className="px-4 py-3 text-end">Crédit</th>
              <th className="px-4 py-3 text-end">Solde progressif</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-900/5">
            {!accountId && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-ink-700">
                  Sélectionnez un compte pour afficher son grand livre.
                </td>
              </tr>
            )}
            {isLoading && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-ink-700">
                  {t("common.loading")}
                </td>
              </tr>
            )}
            {!isLoading && accountId && hasSearched && rows.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-ink-700">
                  Aucun mouvement validé pour ce compte sur la période sélectionnée.
                </td>
              </tr>
            )}
            {!isLoading && rows.map((row, idx) => (
              <tr key={`${row.entry_number}-${idx}`} className="hover:bg-sand-50">
                <td className="px-4 py-3 text-ink-700">{row.entry_date}</td>
                <td className="px-4 py-3">
                  <Link
                    to="/accounting/entries"
                    className="font-mono text-xs font-semibold text-moss-700 hover:underline"
                  >
                    {row.entry_number}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <span className="rounded bg-sand-100 px-2 py-0.5 font-mono text-xs font-semibold text-ink-900">
                    {row.journal_code}
                  </span>
                </td>
                <td className="px-4 py-3 max-w-xs truncate text-ink-700">{row.description || "—"}</td>
                <td className="px-4 py-3 text-end font-medium text-ink-900">
                  {Number(row.debit) > 0 ? formatMoney(row.debit) : "—"}
                </td>
                <td className="px-4 py-3 text-end font-medium text-ink-900">
                  {Number(row.credit) > 0 ? formatMoney(row.credit) : "—"}
                </td>
                <td className={`px-4 py-3 text-end font-semibold ${Number(row.running_balance) >= 0 ? "text-ink-900" : "text-terracotta-600"}`}>
                  {formatMoney(row.running_balance)}
                </td>
              </tr>
            ))}
          </tbody>
          {rows.length > 0 && (
            <tfoot className="border-t-2 border-ink-900/10 bg-sand-50">
              <tr>
                <td colSpan={4} className="px-4 py-3 text-end font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">
                  Totaux
                </td>
                <td className="px-4 py-3 text-end font-bold text-ink-900">{formatMoney(totals.totalDebit.toFixed(2))}</td>
                <td className="px-4 py-3 text-end font-bold text-ink-900">{formatMoney(totals.totalCredit.toFixed(2))}</td>
                <td className="px-4 py-3 text-end font-bold text-ink-900">{formatMoney(totals.closingBalance.toFixed(2))}</td>
              </tr>
            </tfoot>
          )}
        </table>
      </div>
    </div>
  );
}
