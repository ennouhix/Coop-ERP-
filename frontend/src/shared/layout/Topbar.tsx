import { LogOut } from "lucide-react";
import { useTranslation } from "react-i18next";

import { useAuthStore } from "../../features/auth/authStore";

export function Topbar() {
  const { t, i18n } = useTranslation();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  function toggleLanguage() {
    i18n.changeLanguage(i18n.language === "fr" ? "ar" : "fr");
  }

  return (
    <header className="flex h-16 items-center justify-between border-b border-ink-900/5 bg-white px-6">
      <div />
      <div className="flex items-center gap-4">
        <button
          onClick={toggleLanguage}
          className="rounded-md px-2 py-1 text-sm font-medium text-ink-700 hover:bg-sand-100"
          aria-label={t("nav.toggle_language")}
        >
          {i18n.language === "fr" ? "العربية" : "Français"}
        </button>

        <div className="h-6 w-px bg-ink-900/10" />

        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-moss-100 font-display text-sm font-semibold text-moss-700">
            {user?.first_name?.[0]?.toUpperCase() ?? "?"}
          </div>
          <div className="text-start leading-tight">
            <p className="text-sm font-medium text-ink-900">
              {user?.first_name} {user?.last_name}
            </p>
            <p className="text-xs text-ink-700">{t(`roles.${user?.role}`, { defaultValue: user?.role })}</p>
          </div>
        </div>

        <button
          onClick={() => logout()}
          className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium text-ink-700 transition hover:bg-terracotta-500/10 hover:text-terracotta-600"
        >
          <LogOut className="h-4 w-4" />
          {t("auth.logout")}
        </button>
      </div>
    </header>
  );
}
