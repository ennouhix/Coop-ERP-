import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";

import { useAuthStore } from "../../features/auth/authStore";
import { Logo } from "../ui/Logo";
import { NAV_ITEMS, NAV_SECTIONS, type NavItem } from "./navConfig";

function isVisible(item: NavItem, modules: string[]) {
  return !item.module || modules.includes(item.module);
}

export function Sidebar() {
  const { t } = useTranslation();
  const modules = useAuthStore((state) => state.user?.modules) ?? [];

  return (
    <aside className="flex h-screen w-64 shrink-0 flex-col bg-indigo-950 text-indigo-100">
      <div className="relative flex items-center gap-3 px-5 pb-5 pt-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-ochre-500 text-indigo-950 shadow-lift">
          <Logo className="h-5 w-5" />
        </div>
        <div className="leading-tight">
          <span className="block font-display text-base font-bold tracking-tight text-white">{t("app.name")}</span>
          <span className="block font-mono text-[10px] uppercase tracking-eyebrow text-ochre-400/80">ERP · coopératives</span>
        </div>
        <span aria-hidden="true" className="absolute inset-x-5 bottom-0 h-px bg-gradient-to-r from-transparent via-ochre-500/60 to-transparent" />
      </div>

      <nav className="flex-1 space-y-5 overflow-y-auto px-3 pb-4 pt-4">
        {NAV_SECTIONS.map((section) => {
          const items = NAV_ITEMS.filter((item) => item.section === section && isVisible(item, modules));
          if (items.length === 0) return null;
          return (
            <div key={section}>
              <p className="px-3 pb-1.5 font-mono text-[10px] font-medium uppercase tracking-eyebrow text-indigo-400/60">
                {t(`nav.section.${section}`)}
              </p>
              <div className="space-y-0.5">
                {items.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.comingSoon ? "#" : item.to}
                    onClick={(e) => item.comingSoon && e.preventDefault()}
                    className={({ isActive }) =>
                      [
                        "flex items-center gap-3 rounded-md border-s-2 py-2 ps-3 pe-3 text-sm font-medium transition-colors",
                        item.comingSoon
                          ? "cursor-not-allowed text-indigo-400/50"
                          : isActive
                            ? "border-ochre-500 bg-moss-800 text-white"
                            : "border-transparent text-indigo-200 hover:bg-indigo-800/70 hover:text-white",
                      ].join(" ")
                    }
                  >
                    <item.icon className="h-4 w-4 shrink-0" />
                    <span className="flex-1 truncate">{t(item.labelKey)}</span>
                    {item.comingSoon && (
                      <span className="rounded-full bg-indigo-800 px-2 py-0.5 text-[10px] font-medium text-indigo-300">
                        {t("nav.coming_soon")}
                      </span>
                    )}
                  </NavLink>
                ))}
              </div>
            </div>
          );
        })}
      </nav>

      {/* Liseré décoratif bas — motif répété, comme une frise de zellige. */}
      <div className="px-5 pb-4" aria-hidden="true">
        <div className="flex items-center justify-between gap-1 text-ochre-500/25">
          {Array.from({ length: 12 }).map((_, i) => (
            <svg key={i} width="10" height="10" viewBox="0 0 10 10" fill="currentColor">
              <path d="M5 0L10 5L5 10L0 5Z" />
            </svg>
          ))}
        </div>
      </div>
    </aside>
  );
}
