import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";

import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { TextareaField, TextField } from "../../shared/ui/FormField";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { deactivatePartner, getPartner, reactivatePartner, updatePartner } from "./api";
import type { Partner } from "./types";

export function PartnerDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [partner, setPartner] = useState<Partner | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getPartner(id).then(setPartner).finally(() => setIsLoading(false));
  }, [id]);

  function update<K extends keyof Partner>(key: K, value: Partner[K]) {
    setPartner((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  async function handleSave() {
    if (!partner) return;
    setError(null);
    setSuccessMessage(null);

    if (!partner.is_customer && !partner.is_supplier) {
      setError(t("partners.error_role_required"));
      return;
    }

    setIsSaving(true);
    try {
      const updated = await updatePartner(partner.id, {
        is_customer: partner.is_customer, is_supplier: partner.is_supplier,
        name: partner.name, ice: partner.ice,
        phone_number: partner.phone_number, email: partner.email,
        address: partner.address, city: partner.city,
        payment_terms_days: partner.payment_terms_days, credit_limit: partner.credit_limit,
        notes: partner.notes,
      });
      setPartner(updated);
      setSuccessMessage(t("common.saved"));
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleToggleStatus() {
    if (!partner) return;
    setError(null);
    try {
      if (partner.status === "inactive") {
        const updated = await reactivatePartner(partner.id);
        setPartner(updated);
      } else {
        await deactivatePartner(partner.id);
        setPartner({ ...partner, status: "inactive" });
      }
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    }
  }

  if (isLoading) return <p className="text-sm text-ink-700">{t("common.loading")}</p>;
  if (!partner) return <p className="text-sm text-terracotta-600">{t("partners.not_found")}</p>;

  return (
    <div className="mx-auto max-w-2xl">
      <Link to="/partners" className="inline-flex items-center gap-1.5 text-sm text-ink-700 hover:text-ink-900">
        <ArrowLeft className="h-4 w-4" />
        {t("partners.back_to_list")}
      </Link>

      <div className="mt-3 flex items-center justify-between">
        <div>
          <p className="font-mono text-xs text-ink-700/70">{partner.code}</p>
          <h1 className="page-title">{partner.name}</h1>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge label={t(`partners.status_${partner.status}`)} tone={partner.status === "active" ? "moss" : "neutral"} />
          <Button
            variant={partner.status === "inactive" ? "secondary" : "danger"}
            onClick={handleToggleStatus}
          >
            {partner.status === "inactive" ? t("partners.reactivate") : t("partners.deactivate")}
          </Button>
        </div>
      </div>

      <div className="mt-6 space-y-4 card card-pad">
        <div>
          <span className="mb-1 block text-start text-sm font-medium text-ink-800">{t("partners.field.role")}</span>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-sm text-ink-800">
              <input
                type="checkbox" checked={partner.is_customer}
                onChange={(e) => update("is_customer", e.target.checked)}
                className="rounded border-ink-900/25 text-moss-600 focus:ring-moss-500/30"
              />
              {t("partners.role_customer")}
            </label>
            <label className="flex items-center gap-2 text-sm text-ink-800">
              <input
                type="checkbox" checked={partner.is_supplier}
                onChange={(e) => update("is_supplier", e.target.checked)}
                className="rounded border-ink-900/25 text-moss-600 focus:ring-moss-500/30"
              />
              {t("partners.role_supplier")}
            </label>
          </div>
        </div>

        <TextField
          id="name" label={t("partners.field.name")}
          value={partner.name} onChange={(e) => update("name", e.target.value)}
        />

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="phone_number" label={t("partners.field.phone_number")}
            value={partner.phone_number} onChange={(e) => update("phone_number", e.target.value)}
          />
          <TextField
            id="ice" label={t("partners.field.ice")}
            value={partner.ice} onChange={(e) => update("ice", e.target.value)}
          />
        </div>

        <TextField
          id="email" type="email" label={t("partners.field.email")}
          value={partner.email} onChange={(e) => update("email", e.target.value)}
        />

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="address" label={t("partners.field.address")}
            value={partner.address} onChange={(e) => update("address", e.target.value)}
          />
          <TextField
            id="city" label={t("partners.field.city")}
            value={partner.city} onChange={(e) => update("city", e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="payment_terms_days" type="number" min={0} label={t("partners.field.payment_terms_days")}
            value={partner.payment_terms_days} onChange={(e) => update("payment_terms_days", Number(e.target.value))}
          />
          <TextField
            id="credit_limit" type="number" min={0} step="0.01" label={t("partners.field.credit_limit")}
            value={partner.credit_limit} onChange={(e) => update("credit_limit", e.target.value)}
          />
        </div>

        <TextareaField
          id="notes" label={t("partners.field.notes")}
          value={partner.notes} onChange={(e) => update("notes", e.target.value)}
        />

        {error && <p role="alert" className="text-start text-sm text-terracotta-600">{error}</p>}
        {successMessage && <p className="text-start text-sm text-moss-600">{successMessage}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={() => navigate("/partners")}>
            {t("common.cancel")}
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? t("common.loading") : t("common.save")}
          </Button>
        </div>
      </div>
    </div>
  );
}
