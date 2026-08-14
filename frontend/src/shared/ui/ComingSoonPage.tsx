import { useTranslation } from "react-i18next";

import { PageHeader } from "./PageHeader";

export function ComingSoonPage({ titleKey }: { titleKey: string }) {
  const { t } = useTranslation();

  return (
    <div className="mx-auto max-w-xl">
      <PageHeader eyebrow={t("nav.coming_soon")} title={t(titleKey)} />
      <div className="card card-pad mt-6">
        <div className="flex flex-col items-center gap-2 text-center">
          <span className="flex h-10 w-10 items-center justify-center rounded-full border border-ochre-200 bg-ochre-50 text-ochre-600">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1" />
            </svg>
          </span>
          <p className="max-w-sm text-sm leading-relaxed text-ink-700">{t("common.coming_soon_description")}</p>
        </div>
      </div>
    </div>
  );
}
