import { Plus } from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { SelectField, TextField } from "../../shared/ui/FormField";
import { TranslatedTextField } from "../../shared/ui/TranslatedTextField";
import { CatalogTabs } from "./CatalogTabs";
import { createCategory, createUnit, listCategories, listUnits } from "./api";
import type { Category, TranslatedText, Unit, UnitType } from "./types";

const EMPTY_UNIT = { name: "", symbol: "", unit_type: "count" as UnitType };
const EMPTY_CATEGORY: { name: TranslatedText; parent: string | null } = { name: { fr: "", ar: "" }, parent: null };

export function ReferenceDataPage() {
  const { t } = useTranslation();
  const [units, setUnits] = useState<Unit[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [unitForm, setUnitForm] = useState(EMPTY_UNIT);
  const [categoryForm, setCategoryForm] = useState(EMPTY_CATEGORY);
  const [unitError, setUnitError] = useState<string | null>(null);
  const [categoryError, setCategoryError] = useState<string | null>(null);

  function refresh() {
    listUnits().then(setUnits);
    listCategories().then(setCategories);
  }

  useEffect(refresh, []);

  async function handleAddUnit(event: FormEvent) {
    event.preventDefault();
    setUnitError(null);
    try {
      await createUnit(unitForm);
      setUnitForm(EMPTY_UNIT);
      refresh();
    } catch (err) {
      setUnitError(extractApiErrorMessage(err, t("common.error_generic")));
    }
  }

  async function handleAddCategory(event: FormEvent) {
    event.preventDefault();
    setCategoryError(null);
    if (!categoryForm.name.fr) {
      setCategoryError(t("catalog.error_name_fr_required"));
      return;
    }
    try {
      await createCategory(categoryForm);
      setCategoryForm(EMPTY_CATEGORY);
      refresh();
    } catch (err) {
      setCategoryError(extractApiErrorMessage(err, t("common.error_generic")));
    }
  }

  return (
    <div>
      <CatalogTabs />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* --- Unités --- */}
        <section>
          <h2 className="font-display text-lg font-bold text-ink-900">{t("catalog.units_title")}</h2>

          <form onSubmit={handleAddUnit} className="mt-3 space-y-3 card p-4">
            <div className="grid grid-cols-3 gap-2">
              <TextField
                id="unit_name" label={t("catalog.field.unit_name")} required
                value={unitForm.name} onChange={(e) => setUnitForm((p) => ({ ...p, name: e.target.value }))}
              />
              <TextField
                id="unit_symbol" label={t("catalog.field.unit_symbol")} required
                value={unitForm.symbol} onChange={(e) => setUnitForm((p) => ({ ...p, symbol: e.target.value }))}
              />
              <SelectField
                id="unit_type" label={t("catalog.field.unit_type")}
                value={unitForm.unit_type} onChange={(e) => setUnitForm((p) => ({ ...p, unit_type: e.target.value as UnitType }))}
              >
                <option value="weight">{t("catalog.unit_type_weight")}</option>
                <option value="volume">{t("catalog.unit_type_volume")}</option>
                <option value="count">{t("catalog.unit_type_count")}</option>
                <option value="length">{t("catalog.unit_type_length")}</option>
              </SelectField>
            </div>
            {unitError && <p className="text-start text-sm text-terracotta-600">{unitError}</p>}
            <Button type="submit" variant="secondary" className="w-full justify-center">
              <Plus className="h-4 w-4" />
              {t("catalog.add_unit")}
            </Button>
          </form>

          <ul className="mt-3 divide-y divide-ink-900/5 card">
            {units.map((unit) => (
              <li key={unit.id} className="flex items-center justify-between px-4 py-2.5 text-sm">
                <span className="font-medium text-ink-900">{unit.name}</span>
                <span className="font-mono text-xs text-ink-700">{unit.symbol}</span>
              </li>
            ))}
            {units.length === 0 && <li className="px-4 py-6 text-center text-sm text-ink-700">{t("catalog.no_units_yet")}</li>}
          </ul>
        </section>

        {/* --- Catégories --- */}
        <section>
          <h2 className="font-display text-lg font-bold text-ink-900">{t("catalog.categories_title")}</h2>

          <form onSubmit={handleAddCategory} className="mt-3 space-y-3 card p-4">
            <TranslatedTextField
              label={t("catalog.field.category_name")} required
              value={categoryForm.name} onChange={(v) => setCategoryForm((p) => ({ ...p, name: v }))}
            />
            <SelectField
              id="parent_category" label={t("catalog.field.parent_category")}
              value={categoryForm.parent ?? ""} onChange={(e) => setCategoryForm((p) => ({ ...p, parent: e.target.value || null }))}
            >
              <option value="">{t("catalog.no_parent")}</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>{category.name_display}</option>
              ))}
            </SelectField>
            {categoryError && <p className="text-start text-sm text-terracotta-600">{categoryError}</p>}
            <Button type="submit" variant="secondary" className="w-full justify-center">
              <Plus className="h-4 w-4" />
              {t("catalog.add_category")}
            </Button>
          </form>

          <ul className="mt-3 divide-y divide-ink-900/5 card">
            {categories.map((category) => (
              <li key={category.id} className="px-4 py-2.5 text-sm font-medium text-ink-900">
                {category.parent && <span className="text-ink-700/50">↳ </span>}
                {category.name_display}
              </li>
            ))}
            {categories.length === 0 && <li className="px-4 py-6 text-center text-sm text-ink-700">{t("catalog.no_categories_yet")}</li>}
          </ul>
        </section>
      </div>
    </div>
  );
}
