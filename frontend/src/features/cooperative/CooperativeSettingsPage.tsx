import { Building2, Check, Upload, Trash2, X, Mail, Loader2, Bell } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { getMediaUrl } from "../../api/client";
import { Button } from "../../shared/ui/Button";
import { SelectField, TextField } from "../../shared/ui/FormField";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { useAuthStore } from "../auth/authStore";
import {
  deleteCooperativeLogo,
  getCooperative,
  getEmailConfig,
  getNotifications,
  updateCooperative,
  updateEmailConfig,
  uploadCooperativeLogo,
  testEmailConnection,
} from "./api";
import type { Cooperative, CooperativeEmailConfig, CooperativeFormValues, EmailNotification } from "./types";

const PLAN_TONE: Record<string, "moss" | "ochre" | "neutral"> = {
  active: "moss",
  trial: "ochre",
  suspended: "neutral",
  cancelled: "neutral",
};

type Tab = "identity" | "legal" | "contact" | "address" | "preferences" | "email" | "notifications";

export function CooperativeSettingsPage() {
  const { t } = useTranslation();
  const currentUser = useAuthStore((state) => state.user);
  const canEdit = currentUser?.role === "owner" || currentUser?.role === "admin";

  const [coop, setCoop] = useState<Cooperative | null>(null);
  const [form, setForm] = useState<CooperativeFormValues | null>(null);
  const [emailConfig, setEmailConfig] = useState<CooperativeEmailConfig | null>(null);
  const [emailForm, setEmailForm] = useState<Partial<CooperativeEmailConfig> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isSavingEmail, setIsSavingEmail] = useState(false);
  const [isUploadingLogo, setIsUploadingLogo] = useState(false);
  const [saved, setSaved] = useState(false);
  const [savedEmail, setSavedEmail] = useState(false);
  const [error, setError] = useState("");
  const [emailError, setEmailError] = useState("");
  const [activeTab, setActiveTab] = useState<Tab>("identity");
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [isTestingSmtp, setIsTestingSmtp] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [notifications, setNotifications] = useState<EmailNotification[]>([]);
  const [isLoadingNotifications, setIsLoadingNotifications] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    Promise.allSettled([getCooperative(), getEmailConfig()])
      .then(([coopResult, emailResult]) => {
        if (coopResult.status === "fulfilled") {
          const data = coopResult.value;
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
        }
        if (emailResult.status === "fulfilled") {
          const data = emailResult.value;
          setEmailConfig(data);
          setEmailForm({
            smtp_host: data.smtp_host,
            smtp_port: data.smtp_port,
            smtp_username: data.smtp_username,
            smtp_password: data.smtp_password,
            smtp_use_tls: data.smtp_use_tls,
            from_name: data.from_name,
            from_email: data.from_email,
            is_configured: data.is_configured,
          });
        } else {
          setEmailForm({
            smtp_host: "",
            smtp_port: 587,
            smtp_username: "",
            smtp_password: "",
            smtp_use_tls: true,
            from_name: "",
            from_email: "",
            is_configured: false,
          });
        }
      })
      .finally(() => setIsLoading(false));
  }, []);

  function updateField<K extends keyof CooperativeFormValues>(
    key: K,
    value: CooperativeFormValues[K],
  ) {
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
    setError("");
    setIsUploadingLogo(true);
    try {
      const updated = await uploadCooperativeLogo(file);
      setCoop(updated);
      setLogoPreview(null);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : t("common.error_generic");
      setError(msg);
    } finally {
      setIsUploadingLogo(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  function handleLogoPreview(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setLogoPreview(ev.target?.result as string);
    reader.readAsDataURL(file);
  }

  async function handleRemoveLogo() {
    setIsUploadingLogo(true);
    try {
      const updated = await deleteCooperativeLogo();
      setCoop(updated);
      setLogoPreview(null);
    } catch {
      setError(t("common.error_generic"));
    } finally {
      setIsUploadingLogo(false);
    }
  }

  function updateEmailField<K extends keyof CooperativeEmailConfig>(
    key: K,
    value: CooperativeEmailConfig[K],
  ) {
    setEmailForm((prev) => (prev ? { ...prev, [key]: value } : prev));
    setSavedEmail(false);
    setTestResult(null);
  }

  useEffect(() => {
    if (activeTab === "notifications") {
      loadNotifications();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  async function handleEmailSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!emailForm) return;
    setEmailError("");
    setIsSavingEmail(true);
    try {
      const updated = await updateEmailConfig(emailForm);
      setEmailConfig(updated);
      setSavedEmail(true);
    } catch {
      setEmailError(t("common.error_generic"));
    } finally {
      setIsSavingEmail(false);
    }
  }

  async function handleTestSmtp() {
    if (!emailForm) return;
    setEmailError("");
    setIsTestingSmtp(true);
    setTestResult(null);
    try {
      const result = await testEmailConnection(emailForm);
      setTestResult(result);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : t("common.error_generic");
      setTestResult({ success: false, message: msg });
    } finally {
      setIsTestingSmtp(false);
    }
  }

  async function loadNotifications() {
    setIsLoadingNotifications(true);
    try {
      const data = await getNotifications();
      setNotifications(data);
    } catch {
      // silently fail
    } finally {
      setIsLoadingNotifications(false);
    }
  }

  if (isLoading || !coop || !form || !emailForm) {
    return <p className="text-ink-700">{t("common.loading")}</p>;
  }

  const logoUrl = getMediaUrl(coop.logo);
  const displayLogo = logoPreview ?? logoUrl;

  const tabs: { key: Tab; labelKey: string }[] = [
    { key: "identity", labelKey: "cooperative.tab_identity" },
    { key: "legal", labelKey: "cooperative.tab_legal" },
    { key: "contact", labelKey: "cooperative.tab_contact" },
    { key: "address", labelKey: "cooperative.tab_address" },
    { key: "preferences", labelKey: "cooperative.tab_preferences" },
    { key: "email", labelKey: "cooperative.tab_email" },
    { key: "notifications", labelKey: "cooperative.tab_notifications" },
  ];

  return (
    <div className="max-w-5xl">
      <h1 className="page-title">{t("cooperative.title")}</h1>
      <p className="page-heading-subtitle">{t("cooperative.subtitle")}</p>

      {/* ── Section Logo & Abonnement ───────────────────────────── */}
      <div className="mt-6 flex items-center gap-5 card p-5">
        <div className="relative">
          <div className="flex h-20 w-20 items-center justify-center overflow-hidden rounded-lg bg-sand-100">
            {displayLogo ? (
              <img
                src={displayLogo}
                alt={coop.name}
                className="h-full w-full object-cover"
              />
            ) : (
              <Building2 className="h-8 w-8 text-ink-400/50" />
            )}
            {isUploadingLogo && (
              <div className="absolute inset-0 flex items-center justify-center rounded-lg bg-ink-900/40">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
              </div>
            )}
          </div>
          {logoPreview && (
            <button
              type="button"
              onClick={() => {
                setLogoPreview(null);
                if (fileInputRef.current) fileInputRef.current.value = "";
              }}
              className="absolute -right-2 -top-2 rounded-full bg-terracotta-500 p-0.5 text-white shadow hover:bg-terracotta-600"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <p className="truncate font-medium text-ink-900">{coop.name}</p>
          {coop.legal_name && (
            <p className="truncate text-sm text-ink-500">{coop.legal_name}</p>
          )}
          <div className="mt-1.5 flex items-center gap-2">
            <StatusBadge
              label={t(`cooperative.subscription_${coop.subscription_status}`)}
              tone={PLAN_TONE[coop.subscription_status] ?? "neutral"}
            />
            {coop.is_trial_expired && (
              <StatusBadge
                label={t("cooperative.trial_expired")}
                tone="ochre"
              />
            )}
          </div>
        </div>

        {canEdit && (
          <div className="flex items-center gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/webp"
              className="hidden"
              onChange={(e) => {
                handleLogoPreview(e);
                handleLogoChange(e);
              }}
            />
            <Button
              type="button"
              variant="secondary"
              disabled={isUploadingLogo}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="h-4 w-4" />
              {logoUrl
                ? t("cooperative.change_logo")
                : t("cooperative.upload_logo")}
            </Button>
            {logoUrl && (
              <Button
                type="button"
                variant="danger"
                disabled={isUploadingLogo}
                onClick={handleRemoveLogo}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        )}
      </div>

      {/* ── Tabs ────────────────────────────────────────────────── */}
      <div className="mt-6 border-b border-ink-200">
        <nav className="flex gap-1 overflow-x-auto" role="tablist">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              role="tab"
              aria-selected={activeTab === tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? "border-terracotta-500 text-terracotta-700"
                  : "border-transparent text-ink-500 hover:border-ink-300 hover:text-ink-700"
              }`}
            >
              {t(tab.labelKey)}
            </button>
          ))}
        </nav>
      </div>

      {/* ── Formulaire ──────────────────────────────────────────── */}
      <form onSubmit={handleSubmit} className="mt-6 card p-5">
        <fieldset disabled={!canEdit} className="space-y-5">
          {/* Tab: Identité */}
          {activeTab === "identity" && (
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-ink-800">
                {t("cooperative.tab_identity")}
              </h2>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
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
            </div>
          )}

          {/* Tab: Informations légales */}
          {activeTab === "legal" && (
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-ink-800">
                {t("cooperative.tab_legal")}
              </h2>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <TextField
                  id="coop-ice"
                  label={t("cooperative.field.ice")}
                  value={form.ice}
                  onChange={(e) => updateField("ice", e.target.value)}
                  maxLength={15}
                  placeholder="001234567000001"
                />
                <TextField
                  id="coop-rc"
                  label={t("cooperative.field.rc_number")}
                  value={form.rc_number}
                  onChange={(e) => updateField("rc_number", e.target.value)}
                />
              </div>
            </div>
          )}

          {/* Tab: Contact */}
          {activeTab === "contact" && (
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-ink-800">
                {t("cooperative.tab_contact")}
              </h2>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
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
            </div>
          )}

          {/* Tab: Adresse */}
          {activeTab === "address" && (
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-ink-800">
                {t("cooperative.tab_address")}
              </h2>
              <TextField
                id="coop-address"
                label={t("cooperative.field.address")}
                value={form.address}
                onChange={(e) => updateField("address", e.target.value)}
              />
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
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
            </div>
          )}

          {/* Tab: Préférences */}
          {activeTab === "preferences" && (
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-ink-800">
                {t("cooperative.tab_preferences")}
              </h2>
              <SelectField
                id="coop-language"
                label={t("cooperative.field.default_language")}
                value={form.default_language}
                onChange={(e) =>
                  updateField("default_language", e.target.value)
                }
              >
                <option value="fr">Français</option>
                <option value="ar">العربية</option>
              </SelectField>
            </div>
          )}

          {/* Tab: Configuration Email (SMTP) */}
          {activeTab === "email" && (
            <div className="space-y-5">
              <h2 className="text-sm font-semibold text-ink-800">
                {t("cooperative.tab_email")}
              </h2>
              <p className="text-xs text-ink-500">
                {t("cooperative.email_subtitle")}
              </p>

              {/* Activate toggle */}
              <div className="flex items-center gap-3">
                <label className="relative inline-flex cursor-pointer items-center gap-2">
                  <input
                    type="checkbox"
                    checked={emailForm.is_configured}
                    onChange={(e) =>
                      updateEmailField("is_configured", e.target.checked)
                    }
                    className="peer sr-only"
                  />
                  <div className="peer h-6 w-11 rounded-full bg-ink-200 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-all peer-checked:bg-moss-500 peer-checked:after:translate-x-full" />
                </label>
                <span className="text-sm text-ink-700">
                  {t("cooperative.email_use_custom")}
                </span>
              </div>

              {emailForm.is_configured && (
                <>
                  {/* Serveur SMTP */}
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <TextField
                      id="smtp-host"
                      label={t("cooperative.email.smtp_host")}
                      value={emailForm.smtp_host ?? ""}
                      onChange={(e) => updateEmailField("smtp_host", e.target.value)}
                      required
                      placeholder="smtp.gmail.com"
                    />
                    <TextField
                      id="smtp-port"
                      type="number"
                      label={t("cooperative.email.smtp_port")}
                      value={emailForm.smtp_port ?? 587}
                      onChange={(e) =>
                        updateEmailField("smtp_port", Number(e.target.value))
                      }
                      required
                    />
                  </div>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <TextField
                      id="smtp-username"
                      label={t("cooperative.email.smtp_username")}
                      value={emailForm.smtp_username ?? ""}
                      onChange={(e) =>
                        updateEmailField("smtp_username", e.target.value)
                      }
                    />
                    <TextField
                      id="smtp-password"
                      type="password"
                      label={t("cooperative.email.smtp_password")}
                      value={emailForm.smtp_password ?? ""}
                      onChange={(e) =>
                        updateEmailField("smtp_password", e.target.value)
                      }
                    />
                  </div>
                  <div className="flex items-center gap-3">
                    <label className="relative inline-flex cursor-pointer items-center gap-2">
                      <input
                        type="checkbox"
                        checked={emailForm.smtp_use_tls}
                        onChange={(e) =>
                          updateEmailField("smtp_use_tls", e.target.checked)
                        }
                        className="peer sr-only"
                      />
                      <div className="peer h-6 w-11 rounded-full bg-ink-200 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:bg-white after:transition-all peer-checked:bg-moss-500 peer-checked:after:translate-x-full" />
                    </label>
                    <span className="text-sm text-ink-700">
                      {t("cooperative.email.smtp_use_tls")}
                    </span>
                  </div>

                  {/* Expéditeur */}
                  <div className="border-t border-ink-200/50 pt-4">
                    <h3 className="text-xs font-semibold text-ink-600 uppercase tracking-wider">
                      {t("cooperative.email.sender_section")}
                    </h3>
                  </div>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <TextField
                      id="from-name"
                      label={t("cooperative.email.from_name")}
                      value={emailForm.from_name ?? ""}
                      onChange={(e) =>
                        updateEmailField("from_name", e.target.value)
                      }
                      placeholder="Ma Coopérative"
                    />
                    <TextField
                      id="from-email"
                      type="email"
                      label={t("cooperative.email.from_email")}
                      value={emailForm.from_email ?? ""}
                      onChange={(e) =>
                        updateEmailField("from_email", e.target.value)
                      }
                      required
                      placeholder="noreply@ma-cooperative.com"
                    />
                  </div>

                  {/* Test connection */}
                  <div className="flex items-center gap-3 pt-2">
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={handleTestSmtp}
                      disabled={isTestingSmtp}
                    >
                      {isTestingSmtp ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Mail className="h-4 w-4" />
                      )}
                      {t("cooperative.email.test_connection")}
                    </Button>
                    {testResult && (
                      <span
                        className={`text-sm ${
                          testResult.success ? "text-moss-700" : "text-terracotta-600"
                        }`}
                      >
                        {testResult.message}
                      </span>
                    )}
                  </div>
                </>
              )}
            </div>
          )}

          {/* Tab: Journal des notifications */}
          {activeTab === "notifications" && (
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-ink-800">
                {t("cooperative.tab_notifications")}
              </h2>
              <p className="text-xs text-ink-500">
                {t("cooperative.notifications_subtitle")}
              </p>

              <Button
                type="button"
                variant="secondary"
                onClick={loadNotifications}
                disabled={isLoadingNotifications}
              >
                {isLoadingNotifications ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Bell className="h-4 w-4" />
                )}
                {t("cooperative.notifications_refresh")}
              </Button>

              {notifications.length === 0 ? (
                <p className="text-sm text-ink-500">
                  {t("cooperative.notifications_empty")}
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-ink-200 text-left text-xs font-medium text-ink-500 uppercase">
                        <th className="pb-2 pr-4">{t("cooperative.notifications_col_type")}</th>
                        <th className="pb-2 pr-4">{t("cooperative.notifications_col_recipient")}</th>
                        <th className="pb-2 pr-4">{t("cooperative.notifications_col_subject")}</th>
                        <th className="pb-2 pr-4">{t("cooperative.notifications_col_status")}</th>
                        <th className="pb-2">{t("cooperative.notifications_col_date")}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-ink-100">
                      {notifications.map((n) => (
                        <tr key={n.id} className="text-ink-700">
                          <td className="py-2 pr-4 whitespace-nowrap">
                            {n.notification_type_display}
                          </td>
                          <td className="py-2 pr-4">
                            {n.recipient_name || n.recipient_email}
                          </td>
                          <td className="py-2 pr-4 max-w-[200px] truncate">
                            {n.subject}
                          </td>
                          <td className="py-2 pr-4">
                            <StatusBadge
                              label={n.status_display}
                              tone={n.status === "sent" ? "moss" : n.status === "failed" ? "terracotta" : "neutral"}
                            />
                          </td>
                          <td className="py-2 whitespace-nowrap text-ink-500">
                            {new Date(n.created_at).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </fieldset>

        {/* Messages */}
        {error && (
          <p className="mt-4 text-start text-sm text-terracotta-600">
            {error}
          </p>
        )}
        {saved && (
          <div className="mt-4 flex items-center gap-1.5 text-start text-sm text-moss-700">
            <Check className="h-4 w-4" />
            {t("common.saved")}
          </div>
        )}

        {canEdit && activeTab !== "email" && (
          <div className="mt-6 flex justify-end border-t border-ink-200/50 pt-4">
            <Button type="submit" disabled={isSaving}>
              {isSaving ? t("common.loading") : t("common.save")}
            </Button>
          </div>
        )}
      </form>

      {/* Email config has its own form */}
      {activeTab === "email" && canEdit && (
        <form onSubmit={handleEmailSubmit} className="mt-6 card p-5">
          {emailError && (
            <p className="text-start text-sm text-terracotta-600">
              {emailError}
            </p>
          )}
          {savedEmail && (
            <div className="flex items-center gap-1.5 text-start text-sm text-moss-700">
              <Check className="h-4 w-4" />
              {t("common.saved")}
            </div>
          )}
          <div className="mt-4 flex justify-end border-t border-ink-200/50 pt-4">
            <Button type="submit" disabled={isSavingEmail}>
              {isSavingEmail ? t("common.loading") : t("common.save")}
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}
