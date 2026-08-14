import { Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Button } from "../../shared/ui/Button";
import { listEntries, listJournals } from "./api";
import type { AccountingEntry, Journal } from "./types";

import { AccountingSubNav } from "./AccountingSubNav";

function formatMoney(value: string): string {
  return `${Number(value).toLocaleString("fr-MA", { minimumFractionDigits: 2 })} MAD`;
}

function PostedBadge({ isPosted }: { isPosted: boolean }) {
  return isPosted ? (
    <span className="inline-block rounded-full bg-sage-100 px-2 py-0.5 text-xs font-medium text-sage-700">
      Validée ✓
    </span>
  ) : (
    <span className="inline-block rounded-full bg-ochre-100 px-2 py-0.5 text-xs font-medium text-ochre-700">
      Brouillon
    </span>
  );
}

export function JournalEntriesListPage() {
  const { t } = useTranslation();
  const [entries, setEntries] = useState<AccountingEntry[]>([]);
  const [journals, setJournals] = useState<Journal[]>([]);
  const [filterJournal, setFilterJournal] = useState("");
  const [filterPosted, setFilterPosted] = useState<"" | "true" | "false">("");
  const [filterPeriod, setFilterPeriod] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    listJournals().then(setJournals);
  }, []);

  useEffect(() => {
    setIsLoading(true);
    listEntries({
      journal: filterJournal || undefined,
      is_posted: filterPosted === "" ? undefined : filterPosted === "true",
      period: filterPeriod || undefined,
    })
      .then((data) => setEntries(data.results))
      .finally(() => setIsLoading(false));
  }, [filterJournal, filterPosted, filterPeriod]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Écritures Comptables</h1>
          <p className="page-heading-subtitle">Journal général — toutes les écritures</p>
        </div>
        <Link to="/accounting/entries/new">
          <Button>
            <Plus className="h-4 w-4" />
            Nouvelle écriture
          </Button>
        </Link>
      </div>

      {/* Navigation sous-modules unifiée */}
      <AccountingSubNav />

      {/* Filtres */}
      <div className="mt-6 flex flex-wrap items-center gap-3">
        <select
          value={filterJournal}
          onChange={(e) => setFilterJournal(e.target.value)}
          className="input-inline"
        >
          <option value="">Tous les journaux</option>
          {journals.map((j) => (
            <option key={j.id} value={j.id}>{j.code} — {j.name_display}</option>
          ))}
        </select>

        <select
          value={filterPosted}
          onChange={(e) => setFilterPosted(e.target.value as "" | "true" | "false")}
          className="input-inline"
        >
          <option value="">Tous les statuts</option>
          <option value="false">Brouillon</option>
          <option value="true">Validée</option>
        </select>

        <input
          type="text"
          placeholder="Période (ex: 2024-01)"
          value={filterPeriod}
          onChange={(e) => setFilterPeriod(e.target.value)}
          className="input-inline"
        />
      </div>

      {/* Tableau */}
      <div className="mt-4 card">
        <table className="w-full text-start text-sm">
          <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
            <tr>
              <th className="px-4 py-3 text-start">N° Écriture</th>
              <th className="px-4 py-3 text-start">Date</th>
              <th className="px-4 py-3 text-start">Journal</th>
              <th className="px-4 py-3 text-start">Description</th>
              <th className="px-4 py-3 text-end">Débit</th>
              <th className="px-4 py-3 text-end">Crédit</th>
              <th className="px-4 py-3 text-start">Statut</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-900/5">
            {isLoading && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-ink-700">{t("common.loading")}</td></tr>
            )}
            {!isLoading && entries.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-ink-700">Aucune écriture trouvée.</td></tr>
            )}
            {entries.map((entry) => (
              <tr key={entry.id} className="hover:bg-sand-50">
                <td className="px-4 py-3 font-mono text-xs">
                  <Link to={`/accounting/entries/${entry.id}`} className="font-semibold text-moss-700 hover:underline">
                    {entry.entry_number}
                  </Link>
                </td>
                <td className="px-4 py-3 text-ink-700">{entry.entry_date}</td>
                <td className="px-4 py-3">
                  <span className="rounded bg-sand-100 px-2 py-0.5 font-mono text-xs font-semibold text-ink-900">
                    {entry.journal_code}
                  </span>
                </td>
                <td className="px-4 py-3 text-ink-700 max-w-xs truncate">{entry.description || "—"}</td>
                <td className="px-4 py-3 text-end font-medium text-ink-900">{formatMoney(entry.total_debit)}</td>
                <td className="px-4 py-3 text-end font-medium text-ink-900">{formatMoney(entry.total_credit)}</td>
                <td className="px-4 py-3"><PostedBadge isPosted={entry.is_posted} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
