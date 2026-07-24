import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { SelectField, TextareaField, TextField } from "../../shared/ui/FormField";
import { createPartner } from "./api";
import { EMPTY_PARTNER_FORM, type PartnerFormValues } from "./types";

export function PartnerCreatePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [values, setValues] = useState<PartnerFormValues>(EMPTY_PARTNER_FORM);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function update<K extends keyof PartnerFormValues>(key: K, value: PartnerFormValues[K]) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (!values.is_customer && !values.is_supplier) {
      setError(t("partners.error_role_required"));
      return;
    }

    setIsSubmitting(true);
    try {
      const partner = await createPartner(values);
      navigate(`/partners/${partner.id}`);
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="font-display text-2xl font-bold text-ink-900">{t("partners.new")}</h1>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4 rounded-lg border border-ink-900/5 bg-white p-6 shadow-sm">
        <div>
          <span className="mb-1 block text-start text-sm font-medium text-ink-800">{t("partners.field.role")}</span>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-sm text-ink-800">
              <input
                type="checkbox" checked={values.is_customer}
                onChange={(e) => update("is_customer", e.target.checked)}
                className="rounded border-ink-900/25 text-moss-600 focus:ring-moss-500/30"
              />
              {t("partners.role_customer")}
            </label>
            <label className="flex items-center gap-2 text-sm text-ink-800">
              <input
                type="checkbox" checked={values.is_supplier}
                onChange={(e) => update("is_supplier", e.target.checked)}
                className="rounded border-ink-900/25 text-moss-600 focus:ring-moss-500/30"
              />
              {t("partners.role_supplier")}
            </label>
          </div>
        </div>

        <TextField
          id="name" label={t("partners.field.name")} required
          value={values.name} onChange={(e) => update("name", e.target.value)}
        />

        <SelectField
          id="partner_kind" label={t("partners.field.partner_kind")}
          value={values.partner_kind} onChange={(e) => update("partner_kind", e.target.value as PartnerFormValues["partner_kind"])}
        >
          <option value="individual">{t("partners.kind_individual")}</option>
          <option value="company">{t("partners.kind_company")}</option>
        </SelectField>

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="phone_number" label={t("partners.field.phone_number")} required
            value={values.phone_number} onChange={(e) => update("phone_number", e.target.value)}
            placeholder="0612345678"
          />
          <TextField
            id="ice" label={t("partners.field.ice")}
            value={values.ice} onChange={(e) => update("ice", e.target.value)}
            placeholder="001234567000012"
          />
        </div>

        <TextField
          id="email" type="email" label={t("partners.field.email")}
          value={values.email} onChange={(e) => update("email", e.target.value)}
        />

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="address" label={t("partners.field.address")}
            value={values.address} onChange={(e) => update("address", e.target.value)}
          />
          <TextField
            id="city" label={t("partners.field.city")}
            value={values.city} onChange={(e) => update("city", e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="payment_terms_days" type="number" min={0} label={t("partners.field.payment_terms_days")}
            value={values.payment_terms_days} onChange={(e) => update("payment_terms_days", Number(e.target.value))}
          />
          <TextField
            id="credit_limit" type="number" min={0} step="0.01" label={t("partners.field.credit_limit")}
            value={values.credit_limit} onChange={(e) => update("credit_limit", e.target.value)}
          />
        </div>

        <TextareaField
          id="notes" label={t("partners.field.notes")}
          value={values.notes} onChange={(e) => update("notes", e.target.value)}
        />

        {error && <p role="alert" className="text-start text-sm text-terracotta-600">{error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={() => navigate("/partners")}>
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
