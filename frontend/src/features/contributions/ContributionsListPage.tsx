import { Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Button } from "../../shared/ui/Button";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { listContributions } from "./api";
import type { Contribution, ContributionStatus } from "./types";

const STATUS_TONE: Record<ContributionStatus, "ochre" | "moss" | "neutral"> = {
  pending: "ochre",
  paid: "moss",
};

function formatMoney(value: string): string {
  return `${Number(value).toLocaleString("fr-MA", { minimumFractionDigits: 2 })} MAD`;
}

export function ContributionsListPage() {
  const { t } = useTranslation();
  const [contributions, setContributions] = useState<Contribution[]>([]);
  const [count, setCount] = useState(0);
  const [status, setStatus] = useState<ContributionStatus | "">("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    listContributions({ status })
      .then((data) => {
        if (!cancelled) {
          setContributions(data.results);
          setCount(data.count);
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [status]);

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">{t("contributions.title")}</h1>
          <p className="page-heading-subtitle">{t("contributions.count", { count })}</p>
        </div>
        <Link to="/contributions/new">
          <Button>
            <Plus className="h-4 w-4" />
            {t("contributions.new")}
          </Button>
        </Link>
      </div>

      <div className="mt-6 flex gap-3">
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as ContributionStatus | "")}
          className="input-inline"
        >
          <option value="">{t("contributions.status_all")}</option>
          <option value="pending">{t("contributions.status_pending")}</option>
          <option value="paid">{t("contributions.status_paid")}</option>
        </select>
      </div>

      <div className="mt-4 card">
        <table className="w-full text-start text-sm">
          <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
            <tr>
              <th className="px-4 py-3 text-start">{t("contributions.field.member")}</th>
              <th className="px-4 py-3 text-start">{t("contributions.field.product")}</th>
              <th className="px-4 py-3 text-start">{t("contributions.field.quantity")}</th>
              <th className="px-4 py-3 text-start">{t("contributions.field.total_amount")}</th>
              <th className="px-4 py-3 text-start">{t("contributions.field.contribution_date")}</th>
              <th className="px-4 py-3 text-start">{t("contributions.field.status")}</th>
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
            {!isLoading && contributions.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-ink-700">
                  {t("contributions.empty")}
                </td>
              </tr>
            )}
            {contributions.map((contribution) => (
              <tr key={contribution.id} className="hover:bg-sand-50">
                <td className="px-4 py-3">
                  <Link to={`/contributions/${contribution.id}`} className="font-medium text-moss-700 hover:underline">
                    {contribution.member_name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-ink-700">
                  <span className="font-mono text-xs text-ink-700">{contribution.product_sku}</span>{" "}
                  {contribution.product_name}
                </td>
                <td className="px-4 py-3 text-ink-700">{contribution.quantity}</td>
                <td className="px-4 py-3 font-medium text-ink-900">{formatMoney(contribution.total_amount)}</td>
                <td className="px-4 py-3 text-ink-700">{contribution.contribution_date}</td>
                <td className="px-4 py-3">
                  <StatusBadge
                    label={t(`contributions.status_${contribution.status}`)}
                    tone={STATUS_TONE[contribution.status]}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
