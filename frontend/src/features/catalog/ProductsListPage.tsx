import { Plus, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Button } from "../../shared/ui/Button";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { CatalogTabs } from "./CatalogTabs";
import { listProducts } from "./api";
import type { Product } from "./types";

function formatMoney(value: string): string {
  return `${Number(value).toLocaleString("fr-MA", { minimumFractionDigits: 2 })} MAD`;
}

export function ProductsListPage() {
  const { t } = useTranslation();
  const [products, setProducts] = useState<Product[]>([]);
  const [count, setCount] = useState(0);
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    const timeout = setTimeout(() => {
      listProducts({ search })
        .then((data) => {
          if (!cancelled) {
            setProducts(data.results);
            setCount(data.count);
          }
        })
        .finally(() => {
          if (!cancelled) setIsLoading(false);
        });
    }, 300);

    return () => {
      cancelled = true;
      clearTimeout(timeout);
    };
  }, [search]);

  return (
    <div>
      <CatalogTabs />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-ink-900">{t("catalog.tab_products")}</h1>
          <p className="mt-1 text-sm text-ink-700">{t("catalog.count", { count })}</p>
        </div>
        <Link to="/catalog/new">
          <Button>
            <Plus className="h-4 w-4" />
            {t("catalog.new_product")}
          </Button>
        </Link>
      </div>

      <div className="relative mt-6 max-w-sm">
        <Search className="pointer-events-none absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-700/50" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={t("catalog.search_placeholder")}
          className="w-full rounded-md border border-ink-900/15 py-2 ps-9 pe-3 text-sm focus:border-moss-500 focus:outline-none focus:ring-2 focus:ring-moss-500/20"
        />
      </div>

      <div className="mt-4 overflow-hidden rounded-lg border border-ink-900/5 bg-white shadow-sm">
        <table className="w-full text-start text-sm">
          <thead className="bg-sand-100 text-xs font-medium uppercase tracking-wide text-ink-700/70">
            <tr>
              <th className="px-4 py-3 text-start">{t("catalog.field.sku")}</th>
              <th className="px-4 py-3 text-start">{t("catalog.field.name")}</th>
              <th className="px-4 py-3 text-start">{t("catalog.field.category")}</th>
              <th className="px-4 py-3 text-start">{t("catalog.field.sale_price")}</th>
              <th className="px-4 py-3 text-start">{t("catalog.field.status")}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-900/5">
            {isLoading && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-ink-700">{t("common.loading")}</td></tr>
            )}
            {!isLoading && products.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-ink-700">{t("catalog.empty")}</td></tr>
            )}
            {products.map((product) => (
              <tr key={product.id} className="hover:bg-sand-50">
                <td className="px-4 py-3 font-mono text-xs text-ink-700">{product.sku}</td>
                <td className="px-4 py-3">
                  <Link to={`/catalog/${product.id}`} className="font-medium text-moss-700 hover:underline">
                    {product.name_display}
                  </Link>
                </td>
                <td className="px-4 py-3 text-ink-700">{product.category_name_display || "—"}</td>
                <td className="px-4 py-3 text-ink-700">
                  {formatMoney(product.reference_sale_price)} <span className="text-xs text-ink-700/60">/ {product.unit_symbol}</span>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge
                    label={product.is_active ? t("catalog.status_active") : t("catalog.status_inactive")}
                    tone={product.is_active ? "moss" : "neutral"}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
