import { Plus, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Button } from "../../shared/ui/Button";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { listMembers } from "./api";
import type { Member, MemberStatus } from "./types";

const STATUS_TONE: Record<MemberStatus, "moss" | "ochre" | "neutral"> = {
  active: "moss",
  suspended: "ochre",
  inactive: "neutral",
};

export function MembersListPage() {
  const { t } = useTranslation();
  const [members, setMembers] = useState<Member[]>([]);
  const [count, setCount] = useState(0);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<MemberStatus | "">("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    const timeout = setTimeout(() => {
      listMembers({ search, status })
        .then((data) => {
          if (!cancelled) {
            setMembers(data.results);
            setCount(data.count);
          }
        })
        .finally(() => {
          if (!cancelled) setIsLoading(false);
        });
    }, 300); // debounce de la recherche

    return () => {
      cancelled = true;
      clearTimeout(timeout);
    };
  }, [search, status]);

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-ink-900">{t("members.title")}</h1>
          <p className="mt-1 text-sm text-ink-700">{t("members.count", { count })}</p>
        </div>
        <Link to="/members/new">
          <Button>
            <Plus className="h-4 w-4" />
            {t("members.new")}
          </Button>
        </Link>
      </div>

      <div className="mt-6 flex gap-3">
        <div className="relative max-w-sm flex-1">
          <Search className="pointer-events-none absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-700/50" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t("members.search_placeholder")}
            className="w-full rounded-md border border-ink-900/15 py-2 ps-9 pe-3 text-sm focus:border-moss-500 focus:outline-none focus:ring-2 focus:ring-moss-500/20"
          />
        </div>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as MemberStatus | "")}
          className="rounded-md border border-ink-900/15 px-3 py-2 text-sm focus:border-moss-500 focus:outline-none focus:ring-2 focus:ring-moss-500/20"
        >
          <option value="">{t("members.status_all")}</option>
          <option value="active">{t("members.status_active")}</option>
          <option value="suspended">{t("members.status_suspended")}</option>
          <option value="inactive">{t("members.status_inactive")}</option>
        </select>
      </div>

      <div className="mt-4 overflow-hidden rounded-lg border border-ink-900/5 bg-white shadow-sm">
        <table className="w-full text-start text-sm">
          <thead className="bg-sand-100 text-xs font-medium uppercase tracking-wide text-ink-700/70">
            <tr>
              <th className="px-4 py-3 text-start">{t("members.field.member_number")}</th>
              <th className="px-4 py-3 text-start">{t("members.field.full_name")}</th>
              <th className="px-4 py-3 text-start">{t("members.field.phone_number")}</th>
              <th className="px-4 py-3 text-start">{t("members.field.status")}</th>
              <th className="px-4 py-3 text-start">{t("members.field.join_date")}</th>
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
            {!isLoading && members.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-ink-700">
                  {t("members.empty")}
                </td>
              </tr>
            )}
            {members.map((member) => (
              <tr key={member.id} className="hover:bg-sand-50">
                <td className="px-4 py-3 font-mono text-xs text-ink-700">{member.member_number}</td>
                <td className="px-4 py-3">
                  <Link to={`/members/${member.id}`} className="font-medium text-moss-700 hover:underline">
                    {member.full_name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-ink-700">{member.phone_number}</td>
                <td className="px-4 py-3">
                  <StatusBadge label={t(`members.status_${member.status}`)} tone={STATUS_TONE[member.status]} />
                </td>
                <td className="px-4 py-3 text-ink-700">{member.join_date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
