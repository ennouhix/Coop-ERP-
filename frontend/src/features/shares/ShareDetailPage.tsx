import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";

import { StatusBadge } from "../../shared/ui/StatusBadge";
import { getShareTransaction } from "./api";
import type { ShareTransaction, ShareTransactionType } from "./types";

const TYPE_TONE: Record<ShareTransactionType, "moss" | "terracotta" | "neutral"> = {
  subscription: "moss",
  redemption: "terracotta",
};

function formatMoney(value: string): string {
  return `${Number(value).toLocaleString("fr-MA", { minimumFractionDigits: 2 })} MAD`;
}

export function ShareDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();

  const [transaction, setTransaction] = useState<ShareTransaction | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    getShareTransaction(id).then(setTransaction).finally(() => setIsLoading(false));
  }, [id]);

  if (isLoading) return <p className="text-sm text-ink-700">{t("common.loading")}</p>;
  if (!transaction) return <p className="text-sm text-terracotta-600">{t("shares.not_found")}</p>;

  return (
    <div className="mx-auto max-w-2xl">
      <Link to="/shares" className="inline-flex items-center gap-1.5 text-sm text-ink-700 hover:text-ink-900">
        <ArrowLeft className="h-4 w-4" />
        {t("shares.back_to_list")}
      </Link>

      <div className="mt-3 flex items-center justify-between">
        <div>
          <p className="font-mono text-xs text-ink-700/70">{transaction.transaction_date}</p>
          <h1 className="page-title">{transaction.member_name}</h1>
        </div>
        <StatusBadge
          label={t(`shares.type_${transaction.transaction_type}`)}
          tone={TYPE_TONE[transaction.transaction_type]}
        />
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4 card card-pad text-sm">
        <div>
          <span className="text-ink-700/70">{t("shares.field.shares_count")} : </span>
          <span className="font-medium text-ink-900">{transaction.shares_count}</span>
        </div>
        <div>
          <span className="text-ink-700/70">{t("shares.field.amount_per_share")} : </span>
          <span className="font-medium text-ink-900">{formatMoney(transaction.amount_per_share)}</span>
        </div>
        <div>
          <span className="text-ink-700/70">{t("shares.field.total_amount")} : </span>
          <span className="font-semibold text-ink-900">{formatMoney(transaction.total_amount)}</span>
        </div>
        <div>
          <span className="text-ink-700/70">{t("shares.field.transaction_date")} : </span>
          <span className="font-medium text-ink-900">{transaction.transaction_date}</span>
        </div>
      </div>

      {transaction.notes && (
        <p className="mt-4 text-sm text-ink-700">
          <span className="font-medium">{t("shares.field.notes")} : </span>
          {transaction.notes}
        </p>
      )}
    </div>
  );
}
