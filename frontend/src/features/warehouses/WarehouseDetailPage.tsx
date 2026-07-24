import { ArrowLeft, Star } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";

import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { SelectField, TextField } from "../../shared/ui/FormField";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import {
  deactivateWarehouse, getWarehouse, listTeamMembers, reactivateWarehouse, setDefaultWarehouse, updateWarehouse,
} from "./api";
import type { TeamMember, Warehouse } from "./types";

export function WarehouseDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [warehouse, setWarehouse] = useState<Warehouse | null>(null);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    Promise.all([getWarehouse(id), listTeamMembers()])
      .then(([warehouseData, membersData]) => {
        setWarehouse(warehouseData);
        setTeamMembers(membersData);
      })
      .finally(() => setIsLoading(false));
  }, [id]);

  function update<K extends keyof Warehouse>(key: K, value: Warehouse[K]) {
    setWarehouse((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  async function handleSave() {
    if (!warehouse) return;
    setError(null);
    setSuccessMessage(null);
    setIsSaving(true);
    try {
      const updated = await updateWarehouse(warehouse.id, {
        name: warehouse.name, address: warehouse.address, city: warehouse.city,
        phone_number: warehouse.phone_number, manager: warehouse.manager,
      });
      setWarehouse({ ...updated, is_default: warehouse.is_default });
      setSuccessMessage(t("common.saved"));
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleSetDefault() {
    if (!warehouse) return;
    setError(null);
    try {
      const updated = await setDefaultWarehouse(warehouse.id);
      setWarehouse(updated);
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    }
  }

  async function handleToggleStatus() {
    if (!warehouse) return;
    setError(null);
    try {
      if (!warehouse.is_active) {
        const updated = await reactivateWarehouse(warehouse.id);
        setWarehouse(updated);
      } else {
        await deactivateWarehouse(warehouse.id);
        setWarehouse({ ...warehouse, is_active: false });
      }
    } catch (err) {
      // Le backend refuse de désactiver l'entrepôt par défaut : le message
      // d'erreur explicite du service (Epic 7) remonte tel quel ici.
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    }
  }

  if (isLoading) return <p className="text-sm text-ink-700">{t("common.loading")}</p>;
  if (!warehouse) return <p className="text-sm text-terracotta-600">{t("warehouses.not_found")}</p>;

  return (
    <div className="mx-auto max-w-2xl">
      <Link to="/warehouses" className="inline-flex items-center gap-1.5 text-sm text-ink-700 hover:text-ink-900">
        <ArrowLeft className="h-4 w-4" />
        {t("warehouses.back_to_list")}
      </Link>

      <div className="mt-3 flex items-center justify-between">
        <div>
          <p className="font-mono text-xs text-ink-700/70">{warehouse.code}</p>
          <h1 className="flex items-center gap-2 font-display text-2xl font-bold text-ink-900">
            {warehouse.is_default && <Star className="h-5 w-5 fill-ochre-500 text-ochre-500" />}
            {warehouse.name}
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge
            label={warehouse.is_active ? t("warehouses.status_active") : t("warehouses.status_inactive")}
            tone={warehouse.is_active ? "moss" : "neutral"}
          />
          <Button
            variant={warehouse.is_active ? "danger" : "secondary"}
            onClick={handleToggleStatus}
            disabled={warehouse.is_default}
            title={warehouse.is_default ? t("warehouses.cannot_deactivate_default") : undefined}
          >
            {warehouse.is_active ? t("warehouses.deactivate") : t("warehouses.reactivate")}
          </Button>
        </div>
      </div>

      {!warehouse.is_default && (
        <button
          onClick={handleSetDefault}
          className="mt-2 text-start text-xs font-medium text-moss-700 hover:underline"
        >
          {t("warehouses.set_default")}
        </button>
      )}

      <div className="mt-6 space-y-4 rounded-lg border border-ink-900/5 bg-white p-6 shadow-sm">
        <TextField
          id="name" label={t("warehouses.field.name")}
          value={warehouse.name} onChange={(e) => update("name", e.target.value)}
        />

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="address" label={t("warehouses.field.address")}
            value={warehouse.address} onChange={(e) => update("address", e.target.value)}
          />
          <TextField
            id="city" label={t("warehouses.field.city")}
            value={warehouse.city} onChange={(e) => update("city", e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="phone_number" label={t("warehouses.field.phone_number")}
            value={warehouse.phone_number} onChange={(e) => update("phone_number", e.target.value)}
          />
          <SelectField
            id="manager" label={t("warehouses.field.manager")}
            value={warehouse.manager ?? ""} onChange={(e) => update("manager", e.target.value || null)}
          >
            <option value="">{t("warehouses.no_manager")}</option>
            {teamMembers.map((member) => (
              <option key={member.id} value={member.id}>{member.first_name} {member.last_name}</option>
            ))}
          </SelectField>
        </div>

        {error && <p role="alert" className="text-start text-sm text-terracotta-600">{error}</p>}
        {successMessage && <p className="text-start text-sm text-moss-600">{successMessage}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={() => navigate("/warehouses")}>
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
