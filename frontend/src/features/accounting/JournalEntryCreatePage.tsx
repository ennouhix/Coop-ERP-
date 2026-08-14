import { Minus, Plus, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "../../shared/ui/Button";
import { createEntry, listAccounts, listJournals } from "./api";
import type { Account, EntryCreateValues, Journal, LineInput } from "./types";
import { EMPTY_LINE } from "./types";

function formatMoney(value: string): string {
  const n = parseFloat(value) || 0;
  return n.toLocaleString("fr-MA", { minimumFractionDigits: 2 });
}

export function JournalEntryCreatePage() {
  const navigate = useNavigate();
  const [journals, setJournals] = useState<Journal[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState<EntryCreateValues>({
    journal_id: "",
    entry_date: new Date().toISOString().slice(0, 10),
    description: "",
    lines: [{ ...EMPTY_LINE }, { ...EMPTY_LINE }],
  });

  useEffect(() => {
    listJournals().then(setJournals);
    listAccounts().then(setAccounts);
  }, []);

  const totalDebit = useMemo(
    () => form.lines.reduce((sum, l) => sum + (parseFloat(l.debit) || 0), 0),
    [form.lines]
  );
  const totalCredit = useMemo(
    () => form.lines.reduce((sum, l) => sum + (parseFloat(l.credit) || 0), 0),
    [form.lines]
  );
  const isBalanced = Math.abs(totalDebit - totalCredit) < 0.001;
  const diff = Math.abs(totalDebit - totalCredit);

  function updateLine(index: number, field: keyof LineInput, value: string) {
    setForm((prev) => {
      const lines = [...prev.lines];
      lines[index] = { ...lines[index], [field]: value };
      return { ...prev, lines };
    });
  }

  function addLine() {
    setForm((prev) => ({ ...prev, lines: [...prev.lines, { ...EMPTY_LINE }] }));
  }

  function removeLine(index: number) {
    if (form.lines.length <= 2) return;
    setForm((prev) => ({ ...prev, lines: prev.lines.filter((_, i) => i !== index) }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isBalanced) return;
    setIsSubmitting(true);
    setError("");
    try {
      const entry = await createEntry(form);
      navigate(`/accounting/entries/${entry.id}`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message;
      setError(msg || "Une erreur est survenue.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleAutoBalance() {
    if (isBalanced || diff <= 0) return;

    setForm((prev) => {
      const lines = [...prev.lines];
      const lastIdx = lines.length - 1;
      const lastLine = lines[lastIdx];

      if (totalDebit > totalCredit) {
        lines[lastIdx] = {
          ...lastLine,
          credit: diff.toFixed(2),
          debit: "0.00",
        };
      } else {
        lines[lastIdx] = {
          ...lastLine,
          debit: diff.toFixed(2),
          credit: "0.00",
        };
      }
      return { ...prev, lines };
    });
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Nouvelle Écriture Comptable</h1>
          <p className="page-heading-subtitle">Saisissez les lignes débit et crédit. L'écriture doit être équilibrée.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* En-tête de l'écriture */}
        <div className="card p-6">
          <h2 className="mb-4 font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">Informations générales</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="field-label text-xs">Journal *</label>
              <select
                required
                value={form.journal_id}
                onChange={(e) => setForm((p) => ({ ...p, journal_id: e.target.value }))}
                className="input text-xs"
              >
                <option value="">Sélectionner un journal</option>
                {journals.map((j) => (
                  <option key={j.id} value={j.id}>{j.code} — {j.name_display}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="field-label text-xs">Date *</label>
              <input
                type="date"
                required
                value={form.entry_date}
                onChange={(e) => setForm((p) => ({ ...p, entry_date: e.target.value }))}
                className="input text-xs"
              />
            </div>
            <div>
              <label className="field-label text-xs">Description</label>
              <input
                type="text"
                placeholder="Libellé global de l'écriture"
                value={form.description}
                onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
                className="input text-xs"
              />
            </div>
          </div>
        </div>

        {/* Lignes */}
        <div className="card">
          <div className="flex items-center justify-between border-b border-ink-900/5 px-6 py-4">
            <h2 className="font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">Lignes d'écriture</h2>
            {!isBalanced && (
              <button
                type="button"
                onClick={handleAutoBalance}
                className="rounded-lg bg-moss-100 px-3 py-1 text-xs font-semibold text-moss-800 hover:bg-moss-200 transition"
              >
                ⚡ Auto-équilibrer (écart : {formatMoney(String(diff))} MAD)
              </button>
            )}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
                <tr>
                  <th className="px-4 py-3 text-start">Compte</th>
                  <th className="px-4 py-3 text-start">Libellé ligne</th>
                  <th className="px-4 py-3 text-end">Débit (MAD)</th>
                  <th className="px-4 py-3 text-end">Crédit (MAD)</th>
                  <th className="w-10 px-4 py-3 text-center"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-900/5">
                {form.lines.map((line, idx) => (
                  <tr key={idx} className="hover:bg-sand-50/50">
                    <td className="px-4 py-2">
                      <select
                        required
                        value={line.account_id}
                        onChange={(e) => updateLine(idx, "account_id", e.target.value)}
                        className="input text-xs px-2.5 py-1.5"
                      >
                        <option value="">— Choisir un compte —</option>
                        {accounts.map((a) => (
                          <option key={a.id} value={a.id}>{a.code} — {a.name_display}</option>
                        ))}
                      </select>
                    </td>
                    <td className="px-4 py-2">
                      <input
                        type="text"
                        placeholder="Libellé précis de la ligne"
                        value={line.label}
                        onChange={(e) => updateLine(idx, "label", e.target.value)}
                        className="input text-xs px-2.5 py-1.5"
                      />
                    </td>
                    <td className="px-4 py-2">
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={line.debit}
                        onChange={(e) => {
                          updateLine(idx, "debit", e.target.value);
                          if (parseFloat(e.target.value) > 0) updateLine(idx, "credit", "0.00");
                        }}
                        className="input text-end text-xs font-mono px-2.5 py-1.5"
                      />
                    </td>
                    <td className="px-4 py-2">
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={line.credit}
                        onChange={(e) => {
                          updateLine(idx, "credit", e.target.value);
                          if (parseFloat(e.target.value) > 0) updateLine(idx, "debit", "0.00");
                        }}
                        className="input text-end text-xs font-mono px-2.5 py-1.5"
                      />
                    </td>
                    <td className="px-4 py-2 text-center">
                      <button
                        type="button"
                        onClick={() => removeLine(idx)}
                        disabled={form.lines.length <= 2}
                        className="rounded p-1 text-ink-700/40 hover:bg-terracotta-50 hover:text-terracotta-600 disabled:opacity-20"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
              {/* Totaux */}
              <tfoot className="border-t-2 border-ink-900/10 bg-sand-50">
                <tr>
                  <td colSpan={2} className="px-4 py-3 text-end font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">
                    Totaux
                  </td>
                  <td className="px-4 py-3 text-end font-mono font-bold text-ink-900">
                    {formatMoney(String(totalDebit))}
                  </td>
                  <td className="px-4 py-3 text-end font-mono font-bold text-ink-900">
                    {formatMoney(String(totalCredit))}
                  </td>
                  <td />
                </tr>
              </tfoot>
            </table>
          </div>

          <div className="flex flex-wrap items-center justify-between border-t border-ink-900/5 px-6 py-4">
            <button
              type="button"
              onClick={addLine}
              className="flex items-center gap-1.5 text-xs font-semibold text-moss-700 hover:text-moss-900"
            >
              <Plus className="h-4 w-4" /> Ajouter une ligne
            </button>

            {/* Indicateur d'équilibre */}
            <div className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-semibold ${
              isBalanced
                ? "border border-sage-200 bg-sage-50 text-sage-700"
                : "border border-terracotta-200 bg-terracotta-50 text-terracotta-700"
            }`}>
              {isBalanced ? (
                <>✓ Écriture Équilibrée (Σ Débit = Σ Crédit)</>
              ) : (
                <>
                  <Minus className="h-4 w-4" />
                  Déséquilibrée — Écart : {formatMoney(String(diff))} MAD
                </>
              )}
            </div>
          </div>
        </div>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate("/accounting/entries")}
            className="rounded-lg border border-ink-900/15 px-4 py-2 text-sm font-medium text-ink-700 hover:bg-sand-50"
          >
            Annuler
          </button>
          <Button type="submit" disabled={!isBalanced || isSubmitting}>
            {isSubmitting ? "Enregistrement…" : "Enregistrer en brouillon"}
          </Button>
        </div>
      </form>
    </div>
  );
}
