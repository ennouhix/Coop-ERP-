import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { SelectField, TextareaField, TextField } from "../../shared/ui/FormField";
import { createAssembly } from "./api";
import { EMPTY_ASSEMBLY_FORM, type AssemblyFormValues } from "./types";

export function AssemblyCreatePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [values, setValues] = useState<AssemblyFormValues>(EMPTY_ASSEMBLY_FORM);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function update<K extends keyof AssemblyFormValues>(key: K, value: AssemblyFormValues[K]) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const assembly = await createAssembly(values);
      navigate(`/assemblies/${assembly.id}`);
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="page-title">{t("assemblies.new")}</h1>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4 card card-pad">
        <TextField
          id="title" label={t("assemblies.field.title")} required
          value={values.title} onChange={(e) => update("title", e.target.value)}
        />

        <div className="grid grid-cols-2 gap-4">
          <SelectField
            id="assembly_type" label={t("assemblies.field.assembly_type")}
            value={values.assembly_type}
            onChange={(e) => update("assembly_type", e.target.value as AssemblyFormValues["assembly_type"])}
          >
            <option value="ordinary">{t("assemblies.type_ordinary")}</option>
            <option value="extraordinary">{t("assemblies.type_extraordinary")}</option>
          </SelectField>

          <SelectField
            id="status" label={t("assemblies.field.status")}
            value={values.status}
            onChange={(e) => update("status", e.target.value as AssemblyFormValues["status"])}
          >
            <option value="draft">{t("assemblies.status_draft")}</option>
            <option value="scheduled">{t("assemblies.status_scheduled")}</option>
            <option value="done">{t("assemblies.status_done")}</option>
            <option value="cancelled">{t("assemblies.status_cancelled")}</option>
          </SelectField>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="scheduled_date" type="date" label={t("assemblies.field.scheduled_date")} required
            value={values.scheduled_date} onChange={(e) => update("scheduled_date", e.target.value)}
          />
          <TextField
            id="quorum_percent" type="number" min={0} step="0.01" label={t("assemblies.field.quorum_percent")}
            value={values.quorum_percent} onChange={(e) => update("quorum_percent", e.target.value)}
          />
        </div>

        <TextField
          id="location" label={t("assemblies.field.location")}
          value={values.location} onChange={(e) => update("location", e.target.value)}
        />

        <TextareaField
          id="agenda" label={t("assemblies.field.agenda")}
          value={values.agenda} onChange={(e) => update("agenda", e.target.value)}
        />

        <TextareaField
          id="minutes_notes" label={t("assemblies.field.minutes_notes")}
          value={values.minutes_notes} onChange={(e) => update("minutes_notes", e.target.value)}
        />

        {error && <p role="alert" className="text-start text-sm text-terracotta-600">{error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={() => navigate("/assemblies")}>
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
