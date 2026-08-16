import { type FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { SelectField, TextareaField, TextField } from "../../shared/ui/FormField";
import { listMembers } from "../members/api";
import type { Member } from "../members/types";
import { createShareTransaction } from "./api";
import { EMPTY_SHARE_TRANSACTION_FORM, type ShareTransactionFormValues } from "./types";

export function ShareCreatePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [values, setValues] = useState<ShareTransactionFormValues>(EMPTY_SHARE_TRANSACTION_FORM);
  const [members, setMembers] = useState<Member[]>([]);
  const [isLoadingMembers, setIsLoadingMembers] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    listMembers({})
      .then((data) => setMembers(data.results))
      .finally(() => setIsLoadingMembers(false));
  }, []);

  function update<K extends keyof ShareTransactionFormValues>(key: K, value: ShareTransactionFormValues[K]) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const transaction = await createShareTransaction(values);
      navigate(`/shares/${transaction.id}`);
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="page-title">{t("shares.new")}</h1>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4 card card-pad">
        <SelectField
          id="member_id" label={t("shares.field.member")} required
          value={values.member_id}
          onChange={(e) => update("member_id", e.target.value)}
        >
          <option value="">{isLoadingMembers ? t("common.loading") : t("shares.select_member")}</option>
          {members.map((member) => (
            <option key={member.id} value={member.id}>
              {member.member_number} — {member.full_name}
            </option>
          ))}
        </SelectField>

        <SelectField
          id="transaction_type" label={t("shares.field.transaction_type")}
          value={values.transaction_type}
          onChange={(e) => update("transaction_type", e.target.value as ShareTransactionFormValues["transaction_type"])}
        >
          <option value="subscription">{t("shares.type_subscription")}</option>
          <option value="redemption">{t("shares.type_redemption")}</option>
        </SelectField>

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="shares_count" type="number" min={1} label={t("shares.field.shares_count")} required
            value={values.shares_count} onChange={(e) => update("shares_count", Number(e.target.value))}
          />
          <TextField
            id="amount_per_share" type="number" min={0} step="0.01" label={t("shares.field.amount_per_share")} required
            value={values.amount_per_share} onChange={(e) => update("amount_per_share", e.target.value)}
          />
        </div>

        <TextField
          id="transaction_date" type="date" label={t("shares.field.transaction_date")}
          value={values.transaction_date} onChange={(e) => update("transaction_date", e.target.value)}
        />

        <TextareaField
          id="notes" label={t("shares.field.notes")}
          value={values.notes} onChange={(e) => update("notes", e.target.value)}
        />

        {error && <p role="alert" className="text-start text-sm text-terracotta-600">{error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={() => navigate("/shares")}>
            {t("common.cancel")}
          </Button>
          <Button type="submit" disabled={isSubmitting || !values.member_id}>
            {isSubmitting ? t("common.loading") : t("common.save")}
          </Button>
        </div>
      </form>
    </div>
  );
}
