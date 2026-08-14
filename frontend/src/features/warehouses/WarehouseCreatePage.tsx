import { type FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { SelectField, TextField } from "../../shared/ui/FormField";
import { createWarehouse, listTeamMembers } from "./api";
import { EMPTY_WAREHOUSE_FORM, type TeamMember, type WarehouseFormValues } from "./types";

export function WarehouseCreatePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [values, setValues] = useState<WarehouseFormValues>(EMPTY_WAREHOUSE_FORM);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    listTeamMembers().then(setTeamMembers);
  }, []);

  function update<K extends keyof WarehouseFormValues>(key: K, value: WarehouseFormValues[K]) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const warehouse = await createWarehouse(values);
      navigate(`/warehouses/${warehouse.id}`);
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="page-title">{t("warehouses.new")}</h1>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4 card card-pad">
        <TextField
          id="name" label={t("warehouses.field.name")} required
          value={values.name} onChange={(e) => update("name", e.target.value)}
        />

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="address" label={t("warehouses.field.address")}
            value={values.address} onChange={(e) => update("address", e.target.value)}
          />
          <TextField
            id="city" label={t("warehouses.field.city")}
            value={values.city} onChange={(e) => update("city", e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="phone_number" label={t("warehouses.field.phone_number")}
            value={values.phone_number} onChange={(e) => update("phone_number", e.target.value)}
            placeholder="0528123456"
          />
          <SelectField
            id="manager" label={t("warehouses.field.manager")}
            value={values.manager ?? ""} onChange={(e) => update("manager", e.target.value || null)}
          >
            <option value="">{t("warehouses.no_manager")}</option>
            {teamMembers.map((member) => (
              <option key={member.id} value={member.id}>{member.first_name} {member.last_name}</option>
            ))}
          </SelectField>
        </div>

        <label className="flex items-center gap-2 text-sm text-ink-800">
          <input
            type="checkbox" checked={values.is_default}
            onChange={(e) => update("is_default", e.target.checked)}
            className="rounded border-ink-900/25 text-moss-600 focus:ring-moss-500/30"
          />
          {t("warehouses.field.set_as_default")}
        </label>

        {error && <p role="alert" className="text-start text-sm text-terracotta-600">{error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={() => navigate("/warehouses")}>
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
