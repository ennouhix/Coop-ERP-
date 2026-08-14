import { LogOut } from "lucide-react";
import { useTranslation } from "react-i18next";

import { useAuthStore } from "../../features/auth/authStore";

function formatToday(locale: string) {
  return new Intl.DateTimeFormat(locale === "ar" ? "ar-MA" : "fr-FR", {
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(new Date());
}

export function Topbar() {
  const { t, i18n } = useTranslation();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  function toggleLanguage() {
    i18n.changeLanguage(i18n.language === "fr" ? "ar" : "fr");
  }

  return (
    <header className="flex h-16 items-center justify-between border-b border-ink-900/10 bg-sand-50/80 px-6 backdrop-blur">
      <p className="font-mono text-[11px] uppercase tracking-eyebrow text-ink-600/80">{formatToday(i18n.language)}</p>

      <div className="flex items-center gap-4">
        <button
          onClick={toggleLanguage}
          className="rounded-md border border-ink-900/10 bg-white px-3 py-1.5 text-sm font-medium text-ink-700 shadow-card transition hover:border-ochre-500/50 hover:text-ink-900"
          aria-label={t("nav.toggle_language")}
        >
          {i18n.language === "fr" ? "العربية" : "Français"}
        </button>

        <div className="h-6 w-px bg-ink-900/10" />

        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full border border-ochre-200 bg-ochre-100 font-display text-sm font-bold text-ochre-800">
            {user?.first_name?.[0]?.toUpperCase() ?? "?"}
          </div>
          <div className="text-start leading-tight">
            <p className="text-sm font-semibold text-ink-900">
              {user?.first_name} {user?.last_name}
            </p>
            <p className="text-xs text-ink-600">{t(`roles.${user?.role}`, { defaultValue: user?.role })}</p>
          </div>
        </div>

        <button
          onClick={() => logout()}
          className="flex items-center gap-1.5 rounded-md border border-transparent px-3 py-1.5 text-sm font-medium text-ink-700 transition hover:border-terracotta-500/30 hover:bg-terracotta-50 hover:text-terracotta-700"
        >
          <LogOut className="h-4 w-4" />
          {t("auth.logout")}
        </button>
      </div>
    </header>
  );
}
