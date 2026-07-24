import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";

import { NAV_ITEMS } from "./navConfig";

export function Sidebar() {
  const { t } = useTranslation();

  return (
    <aside className="flex h-screen w-64 flex-col bg-indigo-950 text-indigo-100">
      <div className="flex items-center gap-2 px-6 py-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-ochre-500 font-display text-sm font-extrabold text-indigo-950">
          C
        </div>
        <span className="font-display text-lg font-bold text-white">{t("app.name")}</span>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-2">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.comingSoon ? "#" : item.to}
            onClick={(e) => item.comingSoon && e.preventDefault()}
            className={({ isActive }) =>
              [
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                item.comingSoon
                  ? "cursor-not-allowed text-indigo-400/60"
                  : isActive
                    ? "bg-moss-600 text-white"
                    : "text-indigo-200 hover:bg-indigo-800 hover:text-white",
              ].join(" ")
            }
          >
            <item.icon className="h-4 w-4 shrink-0" />
            <span className="flex-1">{t(item.labelKey)}</span>
            {item.comingSoon && (
              <span className="rounded-full bg-indigo-800 px-2 py-0.5 text-[10px] font-medium text-indigo-300">
                {t("nav.coming_soon")}
              </span>
            )}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
