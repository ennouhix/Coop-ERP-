import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";

import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { SelectField, TextField } from "../../shared/ui/FormField";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { TranslatedTextField } from "../../shared/ui/TranslatedTextField";
import { deactivateProduct, getProduct, listCategories, reactivateProduct, updateProduct } from "./api";
import type { Category, Product } from "./types";

export function ProductDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [product, setProduct] = useState<Product | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    Promise.all([getProduct(id), listCategories()])
      .then(([productData, categoriesData]) => {
        setProduct(productData);
        setCategories(categoriesData);
      })
      .finally(() => setIsLoading(false));
  }, [id]);

  function update<K extends keyof Product>(key: K, value: Product[K]) {
    setProduct((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  async function handleSave() {
    if (!product) return;
    setError(null);
    setSuccessMessage(null);
    setIsSaving(true);
    try {
      const updated = await updateProduct(product.id, {
        barcode: product.barcode, name: product.name, category: product.category, unit: product.unit,
        reference_purchase_price: product.reference_purchase_price,
        reference_sale_price: product.reference_sale_price,
        minimum_stock_threshold: product.minimum_stock_threshold,
        description: product.description,
        is_sellable: product.is_sellable, is_purchasable: product.is_purchasable,
      });
      setProduct(updated);
      setSuccessMessage(t("common.saved"));
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleToggleStatus() {
    if (!product) return;
    setError(null);
    try {
      if (!product.is_active) {
        const updated = await reactivateProduct(product.id);
        setProduct(updated);
      } else {
        await deactivateProduct(product.id);
        setProduct({ ...product, is_active: false });
      }
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    }
  }

  if (isLoading) return <p className="text-sm text-ink-700">{t("common.loading")}</p>;
  if (!product) return <p className="text-sm text-terracotta-600">{t("catalog.not_found")}</p>;

  return (
    <div className="mx-auto max-w-2xl">
      <Link to="/catalog" className="inline-flex items-center gap-1.5 text-sm text-ink-700 hover:text-ink-900">
        <ArrowLeft className="h-4 w-4" />
        {t("catalog.back_to_list")}
      </Link>

      <div className="mt-3 flex items-center justify-between">
        <div>
          <p className="font-mono text-xs text-ink-700/70">{product.sku}</p>
          <h1 className="page-title">{product.name_display}</h1>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge
            label={product.is_active ? t("catalog.status_active") : t("catalog.status_inactive")}
            tone={product.is_active ? "moss" : "neutral"}
          />
          <Button variant={product.is_active ? "danger" : "secondary"} onClick={handleToggleStatus}>
            {product.is_active ? t("catalog.deactivate") : t("catalog.reactivate")}
          </Button>
        </div>
      </div>

      <div className="mt-6 space-y-4 card card-pad">
        <TranslatedTextField
          label={t("catalog.field.name")}
          value={product.name} onChange={(v) => update("name", v)}
        />

        <div className="grid grid-cols-2 gap-4">
          <TextField id="unit_symbol" label={t("catalog.field.unit")} value={product.unit_symbol} disabled />
          <SelectField
            id="category" label={t("catalog.field.category")}
            value={product.category ?? ""} onChange={(e) => update("category", e.target.value || null)}
          >
            <option value="">{t("catalog.no_category")}</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>{category.name_display}</option>
            ))}
          </SelectField>
        </div>

        <TextField
          id="barcode" label={t("catalog.field.barcode")}
          value={product.barcode} onChange={(e) => update("barcode", e.target.value)}
        />

        <div className="grid grid-cols-3 gap-4">
          <TextField
            id="reference_purchase_price" type="number" min={0} step="0.01"
            label={t("catalog.field.purchase_price")}
            value={product.reference_purchase_price} onChange={(e) => update("reference_purchase_price", e.target.value)}
          />
          <TextField
            id="reference_sale_price" type="number" min={0} step="0.01"
            label={t("catalog.field.sale_price")}
            value={product.reference_sale_price} onChange={(e) => update("reference_sale_price", e.target.value)}
          />
          <TextField
            id="minimum_stock_threshold" type="number" min={0} step="0.001"
            label={t("catalog.field.min_stock")}
            value={product.minimum_stock_threshold} onChange={(e) => update("minimum_stock_threshold", e.target.value)}
          />
        </div>

        <TranslatedTextField
          label={t("catalog.field.description")} multiline
          value={product.description} onChange={(v) => update("description", v)}
        />

        <div className="flex gap-4">
          <label className="flex items-center gap-2 text-sm text-ink-800">
            <input
              type="checkbox" checked={product.is_sellable}
              onChange={(e) => update("is_sellable", e.target.checked)}
              className="rounded border-ink-900/25 text-moss-600 focus:ring-moss-500/30"
            />
            {t("catalog.field.is_sellable")}
          </label>
          <label className="flex items-center gap-2 text-sm text-ink-800">
            <input
              type="checkbox" checked={product.is_purchasable}
              onChange={(e) => update("is_purchasable", e.target.checked)}
              className="rounded border-ink-900/25 text-moss-600 focus:ring-moss-500/30"
            />
            {t("catalog.field.is_purchasable")}
          </label>
        </div>

        {error && <p role="alert" className="text-start text-sm text-terracotta-600">{error}</p>}
        {successMessage && <p className="text-start text-sm text-moss-600">{successMessage}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={() => navigate("/catalog")}>
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
