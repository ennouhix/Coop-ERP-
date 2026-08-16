import { Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Button } from "../../shared/ui/Button";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { listShareTransactions } from "./api";
import type { ShareTransaction, ShareTransactionType } from "./types";

const TYPE_TONE: Record<ShareTransactionType, "moss" | "terracotta" | "neutral"> = {
  subscription: "moss",
  redemption: "terracotta",
};

function formatMoney(value: string): string {
  return `${Number(value).toLocaleString("fr-MA", { minimumFractionDigits: 2 })} MAD`;
}

export function SharesListPage() {
  const { t } = useTranslation();
  const [transactions, setTransactions] = useState<ShareTransaction[]>([]);
  const [count, setCount] = useState(0);
  const [transactionType, setTransactionType] = useState<ShareTransactionType | "">("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    listShareTransactions({ transaction_type: transactionType })
      .then((data) => {
        if (!cancelled) {
          setTransactions(data.results);
          setCount(data.count);
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [transactionType]);

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">{t("shares.title")}</h1>
          <p className="page-heading-subtitle">{t("shares.count", { count })}</p>
        </div>
        <Link to="/shares/new">
          <Button>
            <Plus className="h-4 w-4" />
            {t("shares.new")}
          </Button>
        </Link>
      </div>

      <div className="mt-6 flex gap-3">
        <select
          value={transactionType}
          onChange={(e) => setTransactionType(e.target.value as ShareTransactionType | "")}
          className="input-inline"
        >
          <option value="">{t("shares.type_all")}</option>
          <option value="subscription">{t("shares.type_subscription")}</option>
          <option value="redemption">{t("shares.type_redemption")}</option>
        </select>
      </div>

      <div className="mt-4 card">
        <table className="w-full text-start text-sm">
          <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
            <tr>
              <th className="px-4 py-3 text-start">{t("shares.field.member")}</th>
              <th className="px-4 py-3 text-start">{t("shares.field.transaction_type")}</th>
              <th className="px-4 py-3 text-start">{t("shares.field.shares_count")}</th>
              <th className="px-4 py-3 text-start">{t("shares.field.amount_per_share")}</th>
              <th className="px-4 py-3 text-start">{t("shares.field.total_amount")}</th>
              <th className="px-4 py-3 text-start">{t("shares.field.transaction_date")}</th>
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
            {!isLoading && transactions.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-ink-700">
                  {t("shares.empty")}
                </td>
              </tr>
            )}
            {transactions.map((transaction) => (
              <tr key={transaction.id} className="hover:bg-sand-50">
                <td className="px-4 py-3">
                  <Link to={`/shares/${transaction.id}`} className="font-medium text-moss-700 hover:underline">
                    {transaction.member_name}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge
                    label={t(`shares.type_${transaction.transaction_type}`)}
                    tone={TYPE_TONE[transaction.transaction_type]}
                  />
                </td>
                <td className="px-4 py-3 text-ink-700">{transaction.shares_count}</td>
                <td className="px-4 py-3 text-ink-700">{formatMoney(transaction.amount_per_share)}</td>
                <td className="px-4 py-3 font-medium text-ink-900">{formatMoney(transaction.total_amount)}</td>
                <td className="px-4 py-3 text-ink-700">{transaction.transaction_date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
