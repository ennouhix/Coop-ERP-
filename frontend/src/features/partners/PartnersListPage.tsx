import { Plus, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Button } from "../../shared/ui/Button";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { listPartners } from "./api";
import type { Partner, PartnerStatus } from "./types";

type RoleFilter = "" | "customer" | "supplier";

export function PartnersListPage() {
  const { t } = useTranslation();
  const [partners, setPartners] = useState<Partner[]>([]);
  const [count, setCount] = useState(0);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<PartnerStatus | "">("");
  const [role, setRole] = useState<RoleFilter>("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    const timeout = setTimeout(() => {
      listPartners({
        search, status,
        is_customer: role === "customer" ? true : undefined,
        is_supplier: role === "supplier" ? true : undefined,
      })
        .then((data) => {
          if (!cancelled) {
            setPartners(data.results);
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
  }, [search, status, role]);

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">{t("partners.title")}</h1>
          <p className="page-heading-subtitle">{t("partners.count", { count })}</p>
        </div>
        <Link to="/partners/new">
          <Button>
            <Plus className="h-4 w-4" />
            {t("partners.new")}
          </Button>
        </Link>
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <div className="relative max-w-sm flex-1">
          <Search className="pointer-events-none absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-700/50" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t("partners.search_placeholder")}
            className="w-full input-search"
          />
        </div>
        <select
          value={role}
          onChange={(e) => setRole(e.target.value as RoleFilter)}
          className="input-inline"
        >
          <option value="">{t("partners.role_all")}</option>
          <option value="customer">{t("partners.role_customer")}</option>
          <option value="supplier">{t("partners.role_supplier")}</option>
        </select>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as PartnerStatus | "")}
          className="input-inline"
        >
          <option value="">{t("partners.status_all")}</option>
          <option value="active">{t("partners.status_active")}</option>
          <option value="inactive">{t("partners.status_inactive")}</option>
        </select>
      </div>

      <div className="mt-4 card">
        <table className="w-full text-start text-sm">
          <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
            <tr>
              <th className="px-4 py-3 text-start">{t("partners.field.code")}</th>
              <th className="px-4 py-3 text-start">{t("partners.field.name")}</th>
              <th className="px-4 py-3 text-start">{t("partners.field.role")}</th>
              <th className="px-4 py-3 text-start">{t("partners.field.phone_number")}</th>
              <th className="px-4 py-3 text-start">{t("partners.field.status")}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-900/5">
            {isLoading && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-ink-700">{t("common.loading")}</td>
              </tr>
            )}
            {!isLoading && partners.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-ink-700">{t("partners.empty")}</td>
              </tr>
            )}
            {partners.map((partner) => (
              <tr key={partner.id} className="hover:bg-sand-50">
                <td className="px-4 py-3 font-mono text-xs text-ink-700">{partner.code}</td>
                <td className="px-4 py-3">
                  <Link to={`/partners/${partner.id}`} className="font-medium text-moss-700 hover:underline">
                    {partner.name}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1.5">
                    {partner.is_customer && <StatusBadge label={t("partners.role_customer")} tone="moss" />}
                    {partner.is_supplier && <StatusBadge label={t("partners.role_supplier")} tone="ochre" />}
                  </div>
                </td>
                <td className="px-4 py-3 text-ink-700">{partner.phone_number}</td>
                <td className="px-4 py-3">
                  <StatusBadge
                    label={t(`partners.status_${partner.status}`)}
                    tone={partner.status === "active" ? "moss" : "neutral"}
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
