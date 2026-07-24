import { useTranslation } from "react-i18next";

export function ComingSoonPage({ titleKey }: { titleKey: string }) {
  const { t } = useTranslation();

  return (
    <div className="flex h-full flex-col items-center justify-center text-center">
      <p className="font-mono text-xs uppercase tracking-widest text-ink-700/60">{t("nav.coming_soon")}</p>
      <h1 className="mt-2 font-display text-2xl font-bold text-ink-900">{t(titleKey)}</h1>
      <p className="mt-2 max-w-sm text-sm text-ink-700">{t("common.coming_soon_description")}</p>
    </div>
  );
}
