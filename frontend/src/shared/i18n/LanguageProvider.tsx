/**
 * Applique dynamiquement dir="rtl"/"ltr" et lang="ar"/"fr" sur <html> à
 * chaque changement de langue. Le reste de l'UI doit utiliser les classes
 * Tailwind logiques (ms-*, me-*, ps-*, pe-*, text-start, text-end) plutôt
 * que left/right pour s'adapter automatiquement au sens de lecture.
 */
import { useEffect, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { RTL_LANGUAGES } from "./config";

export function LanguageProvider({ children }: { children: ReactNode }) {
  const { i18n } = useTranslation();

  useEffect(() => {
    const isRtl = (RTL_LANGUAGES as readonly string[]).includes(i18n.language);
    document.documentElement.setAttribute("dir", isRtl ? "rtl" : "ltr");
    document.documentElement.setAttribute("lang", i18n.language);
  }, [i18n.language]);

  return <>{children}</>;
}
