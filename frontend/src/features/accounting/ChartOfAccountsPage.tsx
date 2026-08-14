import { Plus, Search, BookPlus } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "../../shared/ui/Button";
import { AccountCreateModal } from "./AccountCreateModal";
import { AccountingSubNav } from "./AccountingSubNav";
import { listAccounts } from "./api";
import type { Account, AccountType } from "./types";

const TYPE_LABELS: Record<AccountType, string> = {
  asset: "Actif",
  liability: "Passif",
  equity: "Capitaux propres",
  revenue: "Produit (Cl. 7)",
  expense: "Charge (Cl. 6)",
  treasury: "Trésorerie (Cl. 5)",
};

const TYPE_COLORS: Record<AccountType, string> = {
  asset: "bg-indigo-100 text-indigo-700 border-indigo-200",
  liability: "bg-ochre-100 text-ochre-700 border-ochre-200",
  equity: "bg-aubergine-100 text-aubergine-700 border-aubergine-200",
  revenue: "bg-sage-100 text-sage-700 border-sage-200",
  expense: "bg-terracotta-100 text-terracotta-700 border-terracotta-200",
  treasury: "bg-sage-100 text-sage-700 border-sage-200",
};

function AccountTypeBadge({ type }: { type: AccountType }) {
  return (
    <span className={`inline-block rounded-full border px-2.5 py-0.5 text-xs font-semibold ${TYPE_COLORS[type]}`}>
      {TYPE_LABELS[type]}
    </span>
  );
}

export function ChartOfAccountsPage() {
  const { t } = useTranslation();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [filterType, setFilterType] = useState<AccountType | "">("");
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    setIsLoading(true);
    listAccounts(filterType ? { account_type: filterType } : undefined)
      .then(setAccounts)
      .finally(() => setIsLoading(false));
  }, [filterType]);

  const filteredAccounts = useMemo(() => {
    if (!searchQuery.trim()) return accounts;
    const q = searchQuery.toLowerCase().trim();
    return accounts.filter((a) => {
      const codeMatch = a.code.toLowerCase().includes(q);
      const frMatch = a.name_display.toLowerCase().includes(q);
      const arMatch = a.name?.ar ? a.name.ar.toLowerCase().includes(q) : false;
      return codeMatch || frMatch || arMatch;
    });
  }, [accounts, searchQuery]);

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="page-title">Plan Comptable (PCM)</h1>
          <p className="page-heading-subtitle">
            Plan Comptable Marocain & comptes personnalisés de la coopérative
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <BookPlus className="h-4 w-4" />
          Ajouter un compte
        </Button>
      </div>

      {/* Sous-navigation unifiée */}
      <AccountingSubNav />

      {/* Filtres & Recherche */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Recherche textuelle */}
          <div className="relative min-w-[260px]">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-ink-700/40" />
            <input
              type="text"
              placeholder="Rechercher par code ou libellé..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-search text-xs"
            />
          </div>

          {/* Filtre type */}
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as AccountType | "")}
            className="rounded-lg border border-ink-900/15 px-3 py-2 text-xs font-medium focus:border-moss-500 focus:outline-none focus:ring-2 focus:ring-moss-500/20"
          >
            <option value="">Tous les types</option>
            {(Object.keys(TYPE_LABELS) as AccountType[]).map((t) => (
              <option key={t} value={t}>{TYPE_LABELS[t]}</option>
            ))}
          </select>
        </div>

        <span className="text-xs font-semibold text-ink-700/60">
          {filteredAccounts.length} compte(s) trouvé(s)
        </span>
      </div>

      {/* Tableau du plan comptable */}
      <div className="card">
        <table className="w-full text-start text-xs">
          <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
            <tr>
              <th className="px-4 py-3 text-start">Code PCM</th>
              <th className="px-4 py-3 text-start">Libellé du compte</th>
              <th className="px-4 py-3 text-start">Type</th>
              <th className="px-4 py-3 text-start">Source</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-900/5">
            {isLoading && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-ink-700">
                  {t("common.loading")}
                </td>
              </tr>
            )}
            {!isLoading && filteredAccounts.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-ink-700">
                  Aucun compte trouvé.
                </td>
              </tr>
            )}
            {!isLoading && filteredAccounts.map((account) => (
              <tr key={account.id} className="hover:bg-sand-50">
                <td className="px-4 py-3 font-mono text-xs font-bold text-ink-900">
                  {account.code}
                </td>
                <td className="px-4 py-3 text-ink-800">
                  <span className="font-medium">{account.name_display}</span>
                  {account.name?.ar && (
                    <span className="ms-2 text-xs text-ink-700/50" dir="rtl">{account.name.ar}</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <AccountTypeBadge type={account.account_type} />
                </td>
                <td className="px-4 py-3">
                  {account.is_system ? (
                    <span className="inline-block rounded bg-sand-200 px-2 py-0.5 font-mono text-[10px] font-semibold text-moss-800">
                      PCM officiel
                    </span>
                  ) : (
                    <span className="inline-block rounded bg-indigo-100 px-2 py-0.5 text-[10px] font-semibold text-indigo-700">
                      Personnalisé
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal de création de compte */}
      <AccountCreateModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={(newAccount) => {
          setAccounts((prev) => [newAccount, ...prev].sort((a, b) => a.code.localeCompare(b.code)));
        }}
        existingAccounts={accounts}
      />
    </div>
  );
}
