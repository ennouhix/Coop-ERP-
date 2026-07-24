import { Building2, Upload } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { getMediaUrl } from "../../api/client";
import { Button } from "../../shared/ui/Button";
import { SelectField, TextField } from "../../shared/ui/FormField";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { useAuthStore } from "../auth/authStore";
import { getCooperative, updateCooperative, uploadCooperativeLogo } from "./api";
import type { Cooperative, CooperativeFormValues } from "./types";

const PLAN_TONE: Record<string, "moss" | "ochre" | "neutral"> = {
  active: "moss",
  trial: "ochre",
  suspended: "neutral",
  cancelled: "neutral",
};

export function CooperativeSettingsPage() {
  const { t } = useTranslation();
  const currentUser = useAuthStore((state) => state.user);
  const canEdit = currentUser?.role === "owner" || currentUser?.role === "admin";

  const [coop, setCoop] = useState<Cooperative | null>(null);
  const [form, setForm] = useState<CooperativeFormValues | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isUploadingLogo, setIsUploadingLogo] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getCooperative()
      .then((data) => {
        setCoop(data);
        setForm({
          name: data.name,
          legal_name: data.legal_name,
          ice: data.ice,
          rc_number: data.rc_number,
          email: data.email,
          phone_number: data.phone_number,
          address: data.address,
          city: data.city,
          region: data.region,
          default_language: data.default_language,
        });
      })
      .finally(() => setIsLoading(false));
  }, []);

  function updateField<K extends keyof CooperativeFormValues>(key: K, value: CooperativeFormValues[K]) {
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev));
    setSaved(false);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form) return;
    setError("");
    setIsSaving(true);
    try {
      const updated = await updateCooperative(form);
      setCoop(updated);
      setSaved(true);
    } catch {
      setError(t("common.error_generic"));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleLogoChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploadingLogo(true);
    try {
      const updated = await uploadCooperativeLogo(file);
      setCoop(updated);
    } finally {
      setIsUploadingLogo(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  if (isLoading || !coop || !form) {
    return <p className="text-ink-700">{t("common.loading")}</p>;
  }

  return (
    <div className="max-w-2xl">
      <h1 className="font-display text-2xl font-bold text-ink-900">{t("cooperative.title")}</h1>
      <p className="mt-1 text-sm text-ink-700">{t("cooperative.subtitle")}</p>

      <div className="mt-6 flex items-center gap-4 rounded-lg border border-ink-900/5 bg-white p-5 shadow-sm">
        <div className="flex h-16 w-16 items-center justify-center overflow-hidden rounded-md bg-sand-100">
          {coop.logo ? (
            <img src={getMediaUrl(coop.logo) ?? undefined} alt={coop.name} className="h-full w-full object-cover" />
          ) : (
            <Building2 className="h-7 w-7 text-ink-700/40" />
          )}
        </div>
        <div className="flex-1">
          <p className="font-medium text-ink-900">{coop.name}</p>
          <div className="mt-1 flex items-center gap-2">
            <StatusBadge
              label={t(`cooperative.subscription_${coop.subscription_status}`)}
              tone={PLAN_TONE[coop.subscription_status] ?? "neutral"}
            />
            {coop.is_trial_expired && (
              <StatusBadge label={t("cooperative.trial_expired")} tone="ochre" />
            )}
          </div>
        </div>
        {canEdit && (
          <>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleLogoChange}
            />
            <Button
              type="button"
              variant="secondary"
              disabled={isUploadingLogo}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="h-4 w-4" />
              {t("cooperative.change_logo")}
            </Button>
          </>
        )}
      </div>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4 rounded-lg border border-ink-900/5 bg-white p-5 shadow-sm">
        <fieldset disabled={!canEdit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <TextField
              id="coop-name"
              label={t("cooperative.field.name")}
              value={form.name}
              onChange={(e) => updateField("name", e.target.value)}
              required
            />
            <TextField
              id="coop-legal-name"
              label={t("cooperative.field.legal_name")}
              value={form.legal_name}
              onChange={(e) => updateField("legal_name", e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <TextField
              id="coop-ice"
              label={t("cooperative.field.ice")}
              value={form.ice}
              onChange={(e) => updateField("ice", e.target.value)}
              maxLength={15}
            />
            <TextField
              id="coop-rc"
              label={t("cooperative.field.rc_number")}
              value={form.rc_number}
              onChange={(e) => updateField("rc_number", e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <TextField
              id="coop-email"
              type="email"
              label={t("cooperative.field.email")}
              value={form.email}
              onChange={(e) => updateField("email", e.target.value)}
            />
            <TextField
              id="coop-phone"
              label={t("cooperative.field.phone_number")}
              value={form.phone_number}
              onChange={(e) => updateField("phone_number", e.target.value)}
            />
          </div>
          <TextField
            id="coop-address"
            label={t("cooperative.field.address")}
            value={form.address}
            onChange={(e) => updateField("address", e.target.value)}
          />
          <div className="grid grid-cols-2 gap-4">
            <TextField
              id="coop-city"
              label={t("cooperative.field.city")}
              value={form.city}
              onChange={(e) => updateField("city", e.target.value)}
            />
            <TextField
              id="coop-region"
              label={t("cooperative.field.region")}
              value={form.region}
              onChange={(e) => updateField("region", e.target.value)}
            />
          </div>
          <SelectField
            id="coop-language"
            label={t("cooperative.field.default_language")}
            value={form.default_language}
            onChange={(e) => updateField("default_language", e.target.value)}
          >
            <option value="fr">Français</option>
            <option value="ar">العربية</option>
          </SelectField>
        </fieldset>

        {error && <p className="text-start text-sm text-terracotta-600">{error}</p>}
        {saved && <p className="text-start text-sm text-moss-700">{t("common.saved")}</p>}

        {canEdit && (
          <div className="flex justify-end pt-2">
            <Button type="submit" disabled={isSaving}>
              {t("common.save")}
            </Button>
          </div>
        )}
      </form>
    </div>
  );
}
