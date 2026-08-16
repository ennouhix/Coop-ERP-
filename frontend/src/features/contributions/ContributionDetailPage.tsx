import { ArrowLeft, CheckCircle2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";

import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { getContribution, markContributionPaid } from "./api";
import type { Contribution, ContributionStatus } from "./types";

const STATUS_TONE: Record<ContributionStatus, "ochre" | "moss" | "neutral"> = {
  pending: "ochre",
  paid: "moss",
};

function formatMoney(value: string): string {
  return `${Number(value).toLocaleString("fr-MA", { minimumFractionDigits: 2 })} MAD`;
}

export function ContributionDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();

  const [contribution, setContribution] = useState<Contribution | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMarkingPaid, setIsMarkingPaid] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getContribution(id).then(setContribution).finally(() => setIsLoading(false));
  }, [id]);

  async function handleMarkPaid() {
    if (!contribution) return;
    setError(null);
    setIsMarkingPaid(true);
    try {
      setContribution(await markContributionPaid(contribution.id));
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsMarkingPaid(false);
    }
  }

  if (isLoading) return <p className="text-sm text-ink-700">{t("common.loading")}</p>;
  if (!contribution) return <p className="text-sm text-terracotta-600">{t("contributions.not_found")}</p>;

  return (
    <div className="mx-auto max-w-2xl">
      <Link to="/contributions" className="inline-flex items-center gap-1.5 text-sm text-ink-700 hover:text-ink-900">
        <ArrowLeft className="h-4 w-4" />
        {t("contributions.back_to_list")}
      </Link>

      <div className="mt-3 flex items-center justify-between">
        <div>
          <p className="font-mono text-xs text-ink-700/70">
            {contribution.campaign && <span>{contribution.campaign} · </span>}
            {contribution.contribution_date}
          </p>
          <h1 className="page-title">{contribution.member_name}</h1>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge
            label={t(`contributions.status_${contribution.status}`)}
            tone={STATUS_TONE[contribution.status]}
          />
          {contribution.status === "pending" && (
            <Button onClick={handleMarkPaid} disabled={isMarkingPaid}>
              <CheckCircle2 className="h-4 w-4" />
              {t("contributions.mark_paid")}
            </Button>
          )}
        </div>
      </div>

      {error && <p role="alert" className="mt-3 text-start text-sm text-terracotta-600">{error}</p>}

      <div className="mt-6 card card-pad text-sm">
        <div className="mb-3 text-ink-900">
          <span className="font-mono text-xs text-ink-700">{contribution.product_sku}</span>{" "}
          <span className="font-medium">{contribution.product_name}</span>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-ink-700/70">{t("contributions.field.quantity")} : </span>
            <span className="font-medium text-ink-900">{contribution.quantity}</span>
          </div>
          <div>
            <span className="text-ink-700/70">{t("contributions.field.unit_price")} : </span>
            <span className="font-medium text-ink-900">{formatMoney(contribution.unit_price)}</span>
          </div>
          <div>
            <span className="text-ink-700/70">{t("contributions.field.total_amount")} : </span>
            <span className="font-semibold text-ink-900">{formatMoney(contribution.total_amount)}</span>
          </div>
          <div>
            <span className="text-ink-700/70">{t("contributions.field.contribution_date")} : </span>
            <span className="font-medium text-ink-900">{contribution.contribution_date}</span>
          </div>
          {contribution.payment_date && (
            <div>
              <span className="text-ink-700/70">{t("contributions.field.payment_date")} : </span>
              <span className="font-medium text-ink-900">{contribution.payment_date}</span>
            </div>
          )}
        </div>
      </div>

      {contribution.notes && (
        <p className="mt-4 text-sm text-ink-700">
          <span className="font-medium">{t("contributions.field.notes")} : </span>
          {contribution.notes}
        </p>
      )}
    </div>
  );
}
