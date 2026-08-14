import { ArrowLeft, CheckCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { Button } from "../../shared/ui/Button";
import { getEntry, postEntry } from "./api";
import type { AccountingEntry } from "./types";

function formatMoney(value: string): string {
  return `${Number(value).toLocaleString("fr-MA", { minimumFractionDigits: 2 })} MAD`;
}

export function JournalEntryDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [entry, setEntry] = useState<AccountingEntry | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isPosting, setIsPosting] = useState(false);
  const [postError, setPostError] = useState("");

  useEffect(() => {
    if (!id) return;
    setIsLoading(true);
    getEntry(id).then(setEntry).finally(() => setIsLoading(false));
  }, [id]);

  async function handlePost() {
    if (!entry) return;
    setIsPosting(true);
    setPostError("");
    try {
      const updated = await postEntry(entry.id);
      setEntry(updated);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message;
      setPostError(msg || "Erreur lors de la validation.");
    } finally {
      setIsPosting(false);
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-48 items-center justify-center text-ink-700">
        Chargement…
      </div>
    );
  }

  if (!entry) {
    return (
      <div className="text-center text-ink-700">Écriture introuvable.</div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl">
      {/* En-tête */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <button
            onClick={() => navigate("/accounting/entries")}
            className="mb-2 flex items-center gap-1 text-sm text-ink-700/60 hover:text-ink-900"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Retour aux écritures
          </button>
          <h1 className="page-title">{entry.entry_number}</h1>
          {entry.description && (
            <p className="page-heading-subtitle">{entry.description}</p>
          )}
        </div>
        <div className="flex items-center gap-3">
          {entry.is_posted ? (
            <span className="flex items-center gap-1.5 rounded-full bg-sage-100 px-3 py-1 text-sm font-medium text-sage-700">
              <CheckCircle className="h-4 w-4" /> Validée
            </span>
          ) : (
            <Button onClick={handlePost} disabled={isPosting || !entry.is_balanced}>
              {isPosting ? "Validation…" : "Valider l'écriture"}
            </Button>
          )}
        </div>
      </div>

      {/* Cartes d'infos */}
      <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          { label: "Journal", value: entry.journal_code },
          { label: "Date", value: entry.entry_date },
          { label: "Période", value: entry.period },
          {
            label: "Équilibre",
            value: entry.is_balanced ? "✓ Équilibrée" : "⚠ Déséquilibrée",
            className: entry.is_balanced ? "text-sage-700" : "text-terracotta-600",
          },
        ].map((card) => (
          <div key={card.label} className="card p-4">
            <p className="font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">{card.label}</p>
            <p className={`mt-1 text-sm font-semibold text-ink-900 ${card.className ?? ""}`}>{card.value}</p>
          </div>
        ))}
      </div>

      {/* Erreur de validation */}
      {postError && (
        <div className="mb-4 alert alert-error">
          {postError}
        </div>
      )}
      {!entry.is_posted && !entry.is_balanced && (
        <div className="mb-4 alert alert-warn">
          ⚠ Cette écriture ne peut pas être validée car elle n'est pas équilibrée (Σ débit ≠ Σ crédit).
        </div>
      )}

      {/* Tableau des lignes */}
      <div className="card">
        <div className="px-6 py-4 border-b border-ink-900/5">
          <h2 className="font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">Lignes d'écriture</h2>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
            <tr>
              <th className="px-4 py-3 text-start">Compte</th>
              <th className="px-4 py-3 text-start">Libellé</th>
              <th className="px-4 py-3 text-end">Débit</th>
              <th className="px-4 py-3 text-end">Crédit</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-900/5">
            {entry.lines.map((line) => (
              <tr key={line.id} className="hover:bg-sand-50">
                <td className="px-4 py-3">
                  <span className="font-mono text-xs font-semibold text-ink-900">{line.account_code}</span>
                  <span className="ms-2 text-xs text-ink-700/70">{line.account_name}</span>
                </td>
                <td className="px-4 py-3 text-ink-700 text-xs">{line.label || "—"}</td>
                <td className="px-4 py-3 text-end font-medium text-ink-900">
                  {Number(line.debit) > 0 ? formatMoney(line.debit) : "—"}
                </td>
                <td className="px-4 py-3 text-end font-medium text-ink-900">
                  {Number(line.credit) > 0 ? formatMoney(line.credit) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot className="border-t-2 border-ink-900/10 bg-sand-50">
            <tr>
              <td colSpan={2} className="px-4 py-3 text-end font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">
                Totaux
              </td>
              <td className="px-4 py-3 text-end font-bold text-ink-900">{formatMoney(entry.total_debit)}</td>
              <td className="px-4 py-3 text-end font-bold text-ink-900">{formatMoney(entry.total_credit)}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
