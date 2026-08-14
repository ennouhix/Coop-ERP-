import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";

export function CatalogTabs() {
  const { t } = useTranslation();
  const tabClass = ({ isActive }: { isActive: boolean }) =>
    [
      "border-b-2 px-1 pb-3 text-sm font-medium transition",
      isActive ? "border-ochre-500 text-moss-800" : "border-transparent text-ink-700 hover:text-ink-900",
    ].join(" ");

  return (
    <nav className="mb-6 flex gap-6 border-b border-ink-900/10">
      <NavLink to="/catalog" end className={tabClass}>
        {t("catalog.tab_products")}
      </NavLink>
      <NavLink to="/catalog/reference-data" className={tabClass}>
        {t("catalog.tab_reference_data")}
      </NavLink>
    </nav>
  );
}
