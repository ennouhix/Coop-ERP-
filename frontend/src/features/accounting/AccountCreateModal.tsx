import { X } from "lucide-react";
import { useState } from "react";

import { Button } from "../../shared/ui/Button";
import { createAccount } from "./api";
import type { Account, AccountType } from "./types";

const ACCOUNT_TYPES: { value: AccountType; label: string }[] = [
  { value: "asset", label: "Actif (Immobilisations, Stocks, Créances)" },
  { value: "liability", label: "Passif (Dettes, Fournisseurs)" },
  { value: "equity", label: "Capitaux Propres (Capital, Réserves)" },
  { value: "revenue", label: "Produits (Ventes, Subventions - Cl. 7)" },
  { value: "expense", label: "Charges (Achats, Services, Salaires - Cl. 6)" },
  { value: "treasury", label: "Trésorerie (Banque, Caisse - Cl. 5)" },
];

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (newAccount: Account) => void;
  existingAccounts: Account[];
}

export function AccountCreateModal({ isOpen, onClose, onSuccess, existingAccounts }: Props) {
  const [code, setCode] = useState("");
  const [nameFr, setNameFr] = useState("");
  const [nameAr, setNameAr] = useState("");
  const [accountType, setAccountType] = useState<AccountType>("expense");
  const [parentId, setParentId] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  if (!isOpen) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);
    setError("");

    try {
      const created = await createAccount({
        code: code.trim(),
        name: { fr: nameFr.trim(), ar: nameAr.trim() },
        account_type: accountType,
        parent: parentId || null,
      });
      onSuccess(created);
      onClose();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message;
      setError(msg || "Erreur lors de la création du compte.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/50 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg card card-pad shadow-lift">
        <div className="flex items-center justify-between border-b border-ink-900/10 pb-3">
          <h2 className="font-display text-lg font-bold text-ink-900">Ajouter un Compte Comptable</h2>
          <button onClick={onClose} className="rounded-lg p-1 text-ink-700/50 hover:bg-sand-100 hover:text-ink-900">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {error && (
            <div className="alert alert-error p-3 text-xs">
              {error}
            </div>
          )}

          <div>
            <label className="field-label text-xs">Code du Compte *</label>
            <input
              type="text"
              required
              placeholder="ex: 514101"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="input font-mono"
            />
          </div>

          <div>
            <label className="field-label text-xs">Libellé (Français) *</label>
            <input
              type="text"
              required
              placeholder="ex: Banque BMCE - Compte Principal"
              value={nameFr}
              onChange={(e) => setNameFr(e.target.value)}
              className="input"
            />
          </div>

          <div>
            <label className="field-label text-xs">Libellé (Arabe - optionnel)</label>
            <input
              type="text"
              dir="rtl"
              placeholder="ex: البنك المغربي للتجارة الخارجية"
              value={nameAr}
              onChange={(e) => setNameAr(e.target.value)}
              className="input"
            />
          </div>

          <div>
            <label className="field-label text-xs">Type de Compte *</label>
            <select
              value={accountType}
              onChange={(e) => setAccountType(e.target.value as AccountType)}
              className="input"
            >
              {ACCOUNT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="field-label text-xs">Compte Parent (Optionnel)</label>
            <select
              value={parentId}
              onChange={(e) => setParentId(e.target.value)}
              className="input"
            >
              <option value="">Aucun parent</option>
              {existingAccounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.code} — {a.name_display}
                </option>
              ))}
            </select>
          </div>

          <div className="mt-6 flex justify-end gap-2 border-t border-ink-900/10 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-ink-900/15 px-4 py-2 text-sm font-medium text-ink-700 hover:bg-sand-50"
            >
              Annuler
            </button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Création..." : "Créer le compte"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
