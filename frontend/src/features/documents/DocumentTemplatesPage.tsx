import { FileText, Save } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { TextareaField, TextField } from "../../shared/ui/FormField";
import { useAuthStore } from "../auth/authStore";
import { getDocumentTemplates, updateDocumentTemplate } from "./api";
import type { DocumentTemplate, DocumentTemplateFormValues } from "./types";

export function DocumentTemplatesPage() {
  const { t } = useTranslation();
  const currentUser = useAuthStore((state) => state.user);
  const canEdit = currentUser?.role === "owner" || currentUser?.role === "admin";

  const [templates, setTemplates] = useState<DocumentTemplate[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState<string | null>(null);
  const [savedType, setSavedType] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDocumentTemplates()
      .then(setTemplates)
      .catch((err) => setError(extractApiErrorMessage(err, t("common.error_generic"))))
      .finally(() => setIsLoading(false));
  }, [t]);

  function updateField(type: string, key: keyof DocumentTemplateFormValues, value: string | boolean) {
    setTemplates((prev) =>
      prev?.map((template) => {
        if (template.template_type !== type) return template;
        return { ...template, [key]: value } as DocumentTemplate;
      }) ?? prev
    );
    setSavedType(null);
  }

  async function handleSave(template: DocumentTemplate) {
    setError(null);
    setIsSaving(template.template_type);
    try {
      const updated = await updateDocumentTemplate(template.template_type, {
        header_text: template.header_text,
        footer_text: template.footer_text,
        terms_text: template.terms_text,
        accent_color: template.accent_color,
        show_logo: template.show_logo,
      });
      setTemplates((prev) =>
        prev?.map((item) => (item.template_type === updated.template_type ? updated : item)) ?? prev
      );
      setSavedType(updated.template_type);
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSaving(null);
    }
  }

  if (isLoading) return <p className="text-sm text-ink-700">{t("common.loading")}</p>;

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="page-title">{t("documents.templates_title")}</h1>
      <p className="page-heading-subtitle">{t("documents.templates_subtitle")}</p>

      {error && <p role="alert" className="mt-3 text-start text-sm text-terracotta-600">{error}</p>}

      <div className="mt-6 space-y-6">
        {templates?.map((template) => (
          <div key={template.template_type} className="card p-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-moss-600" />
                <h2 className="font-semibold text-ink-900">{template.template_type_label}</h2>
              </div>
              {savedType === template.template_type && (
                <p className="text-sm text-moss-700">{t("common.saved")}</p>
              )}
            </div>

            <fieldset disabled={!canEdit} className="mt-4 space-y-4">
              <TextField
                id={`${template.template_type}-header`}
                label={t("documents.field.header_text")}
                value={template.header_text}
                onChange={(e) => updateField(template.template_type, "header_text", e.target.value)}
              />
              <TextField
                id={`${template.template_type}-footer`}
                label={t("documents.field.footer_text")}
                value={template.footer_text}
                onChange={(e) => updateField(template.template_type, "footer_text", e.target.value)}
              />
              <TextareaField
                id={`${template.template_type}-terms`}
                label={t("documents.field.terms_text")}
                value={template.terms_text}
                onChange={(e) => updateField(template.template_type, "terms_text", e.target.value)}
              />
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor={`${template.template_type}-color`} className="mb-1 block text-start text-sm font-medium text-ink-800">
                    {t("documents.field.accent_color")}
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      id={`${template.template_type}-color`}
                      value={/^#[0-9a-fA-F]{6}$/.test(template.accent_color) ? template.accent_color : "#2e6ff2"}
                      onChange={(e) => updateField(template.template_type, "accent_color", e.target.value)}
                      className="h-10 w-12 cursor-pointer rounded-md border border-ink-900/15"
                    />
                    <input
                      type="text"
                      value={template.accent_color}
                      placeholder="#2e6ff2"
                      maxLength={7}
                      onChange={(e) => updateField(template.template_type, "accent_color", e.target.value)}
                      className="w-32 input-inline"
                    />
                  </div>
                </div>
                <label className="flex items-center gap-2 pt-6 text-sm text-ink-800">
                  <input
                    type="checkbox"
                    checked={template.show_logo}
                    onChange={(e) => updateField(template.template_type, "show_logo", e.target.checked)}
                    className="h-4 w-4 rounded border-ink-900/20 text-moss-600 focus:ring-moss-500/30"
                  />
                  {t("documents.field.show_logo")}
                </label>
              </div>
            </fieldset>

            {canEdit && (
              <div className="mt-4 flex justify-end">
                <Button
                  type="button"
                  disabled={isSaving === template.template_type}
                  onClick={() => handleSave(template)}
                >
                  <Save className="h-4 w-4" />
                  {t("common.save")}
                </Button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
