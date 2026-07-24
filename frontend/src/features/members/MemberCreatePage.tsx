import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { Button } from "../../shared/ui/Button";
import { SelectField, TextareaField, TextField } from "../../shared/ui/FormField";
import { extractApiErrorMessage } from "../../shared/api/errors";
import { createMember } from "./api";
import { EMPTY_MEMBER_FORM, type MemberFormValues } from "./types";

export function MemberCreatePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [values, setValues] = useState<MemberFormValues>(EMPTY_MEMBER_FORM);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function update<K extends keyof MemberFormValues>(key: K, value: MemberFormValues[K]) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const member = await createMember(values);
      navigate(`/members/${member.id}`);
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="font-display text-2xl font-bold text-ink-900">{t("members.new")}</h1>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4 rounded-lg border border-ink-900/5 bg-white p-6 shadow-sm">
        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="first_name" label={t("members.field.first_name")} required
            value={values.first_name} onChange={(e) => update("first_name", e.target.value)}
          />
          <TextField
            id="last_name" label={t("members.field.last_name")} required
            value={values.last_name} onChange={(e) => update("last_name", e.target.value)}
          />
        </div>

        <SelectField
          id="member_type" label={t("members.field.member_type")}
          value={values.member_type} onChange={(e) => update("member_type", e.target.value as MemberFormValues["member_type"])}
        >
          <option value="individual">{t("members.type_individual")}</option>
          <option value="entity">{t("members.type_entity")}</option>
        </SelectField>

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="phone_number" label={t("members.field.phone_number")} required
            value={values.phone_number} onChange={(e) => update("phone_number", e.target.value)}
            placeholder="0612345678"
          />
          <TextField
            id="cin" label={t("members.field.cin")}
            value={values.cin} onChange={(e) => update("cin", e.target.value.toUpperCase())}
            placeholder="AB123456"
          />
        </div>

        <TextField
          id="email" type="email" label={t("members.field.email")}
          value={values.email} onChange={(e) => update("email", e.target.value)}
        />

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="address" label={t("members.field.address")}
            value={values.address} onChange={(e) => update("address", e.target.value)}
          />
          <TextField
            id="city" label={t("members.field.city")}
            value={values.city} onChange={(e) => update("city", e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="join_date" type="date" label={t("members.field.join_date")}
            value={values.join_date} onChange={(e) => update("join_date", e.target.value)}
          />
          <TextField
            id="shares_count" type="number" min={0} label={t("members.field.shares_count")}
            value={values.shares_count} onChange={(e) => update("shares_count", Number(e.target.value))}
          />
        </div>

        <TextareaField
          id="notes" label={t("members.field.notes")}
          value={values.notes} onChange={(e) => update("notes", e.target.value)}
        />

        {error && <p role="alert" className="text-start text-sm text-terracotta-600">{error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={() => navigate("/members")}>
            {t("common.cancel")}
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? t("common.loading") : t("common.save")}
          </Button>
        </div>
      </form>
    </div>
  );
}
