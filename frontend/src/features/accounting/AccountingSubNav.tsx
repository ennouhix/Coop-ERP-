import {
  LayoutDashboard,
  BookOpen,
  FileSpreadsheet,
  BookMarked,
  Scale,
  PieChart,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";

export function AccountingSubNav() {
  const location = useLocation();

  const NAV_ITEMS = [
    { to: "/accounting", label: "Vue d'ensemble", icon: LayoutDashboard, exact: true },
    { to: "/accounting/accounts", label: "Plan comptable", icon: BookOpen },
    { to: "/accounting/entries", label: "Écritures", icon: FileSpreadsheet },
    { to: "/accounting/ledger", label: "Grand livre", icon: BookMarked },
    { to: "/accounting/trial-balance", label: "Balance", icon: Scale },
    { to: "/accounting/statements", label: "CPC & Bilan", icon: PieChart },
  ];

  return (
    <div className="mt-4 flex gap-1 overflow-x-auto border-b border-ink-900/10 pb-0 print:hidden">
      {NAV_ITEMS.map((item) => {
        const isActive = item.exact
          ? location.pathname === item.to
          : location.pathname.startsWith(item.to);
        const Icon = item.icon;

        return (
          <Link
            key={item.to}
            to={item.to}
            className={`-mb-px flex shrink-0 items-center gap-2 border-b-2 px-3.5 py-2.5 text-sm font-medium transition ${
              isActive
                ? "border-ochre-500 text-moss-800"
                : "border-transparent text-ink-600 hover:border-ink-900/20 hover:text-ink-900"
            }`}
          >
            <Icon className="h-4 w-4" />
            {item.label}
          </Link>
        );
      })}
    </div>
  );
}
