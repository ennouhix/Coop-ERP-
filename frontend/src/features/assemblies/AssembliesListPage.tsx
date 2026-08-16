import { Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Button } from "../../shared/ui/Button";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { listAssemblies } from "./api";
import type { Assembly, AssemblyStatus } from "./types";

const STATUS_TONE: Record<AssemblyStatus, "moss" | "ochre" | "neutral" | "terracotta"> = {
  draft: "neutral",
  scheduled: "ochre",
  done: "moss",
  cancelled: "terracotta",
};

const TYPE_LABEL: Record<Assembly["assembly_type"], string> = {
  ordinary: "assemblies.type_ordinary",
  extraordinary: "assemblies.type_extraordinary",
};

export function AssembliesListPage() {
  const { t } = useTranslation();
  const [assemblies, setAssemblies] = useState<Assembly[]>([]);
  const [count, setCount] = useState(0);
  const [status, setStatus] = useState<AssemblyStatus | "">("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    listAssemblies({ status })
      .then((data) => {
        if (!cancelled) {
          setAssemblies(data.results);
          setCount(data.count);
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [status]);

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">{t("assemblies.title")}</h1>
          <p className="page-heading-subtitle">{t("assemblies.count", { count })}</p>
        </div>
        <Link to="/assemblies/new">
          <Button>
            <Plus className="h-4 w-4" />
            {t("assemblies.new")}
          </Button>
        </Link>
      </div>

      <div className="mt-6 flex gap-3">
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as AssemblyStatus | "")}
          className="input-inline"
        >
          <option value="">{t("assemblies.status_all")}</option>
          <option value="draft">{t("assemblies.status_draft")}</option>
          <option value="scheduled">{t("assemblies.status_scheduled")}</option>
          <option value="done">{t("assemblies.status_done")}</option>
          <option value="cancelled">{t("assemblies.status_cancelled")}</option>
        </select>
      </div>

      <div className="mt-4 card">
        <table className="w-full text-start text-sm">
          <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
            <tr>
              <th className="px-4 py-3 text-start">{t("assemblies.field.title")}</th>
              <th className="px-4 py-3 text-start">{t("assemblies.field.assembly_type")}</th>
              <th className="px-4 py-3 text-start">{t("assemblies.field.scheduled_date")}</th>
              <th className="px-4 py-3 text-start">{t("assemblies.field.presence")}</th>
              <th className="px-4 py-3 text-start">{t("assemblies.field.status")}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-900/5">
            {isLoading && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-ink-700">
                  {t("common.loading")}
                </td>
              </tr>
            )}
            {!isLoading && assemblies.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-ink-700">
                  {t("assemblies.empty")}
                </td>
              </tr>
            )}
            {assemblies.map((assembly) => (
              <tr key={assembly.id} className="hover:bg-sand-50">
                <td className="px-4 py-3">
                  <Link to={`/assemblies/${assembly.id}`} className="font-medium text-moss-700 hover:underline">
                    {assembly.title}
                  </Link>
                </td>
                <td className="px-4 py-3 text-ink-700">{t(TYPE_LABEL[assembly.assembly_type])}</td>
                <td className="px-4 py-3 text-ink-700">{assembly.scheduled_date}</td>
                <td className="px-4 py-3 text-ink-700">
                  {assembly.present_count} / {assembly.attendances_count}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge label={t(`assemblies.status_${assembly.status}`)} tone={STATUS_TONE[assembly.status]} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
