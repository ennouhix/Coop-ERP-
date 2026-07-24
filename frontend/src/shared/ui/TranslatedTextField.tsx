import { useTranslation } from "react-i18next";

import type { TranslatedText } from "../../features/catalog/types";

interface TranslatedTextFieldProps {
  label: string;
  value: TranslatedText;
  onChange: (value: TranslatedText) => void;
  multiline?: boolean;
  required?: boolean;
}

/**
 * Édite un champ TranslatedField (apps.core.fields côté Django) : deux
 * champs côte à côte, FR obligatoire, AR optionnel. Le champ AR utilise
 * dir="rtl" indépendamment de la langue active de l'interface — on édite
 * du contenu arabe même quand l'app est affichée en français.
 */
export function TranslatedTextField({ label, value, onChange, multiline = false, required = false }: TranslatedTextFieldProps) {
  const { t } = useTranslation();
  const Tag = multiline ? "textarea" : "input";

  return (
    <div>
      <span className="mb-1 block text-start text-sm font-medium text-ink-800">
        {label} {required && <span className="text-terracotta-600">*</span>}
      </span>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-0.5 block text-start text-xs text-ink-700/70">{t("catalog.lang_fr")}</label>
          <Tag
            required={required}
            rows={multiline ? 2 : undefined}
            value={value.fr}
            onChange={(e) => onChange({ ...value, fr: e.target.value })}
            className="w-full rounded-md border border-ink-900/15 px-3 py-2 text-start text-sm focus:border-moss-500 focus:outline-none focus:ring-2 focus:ring-moss-500/20"
          />
        </div>
        <div>
          <label className="mb-0.5 block text-start text-xs text-ink-700/70">{t("catalog.lang_ar")}</label>
          <Tag
            rows={multiline ? 2 : undefined}
            dir="rtl"
            value={value.ar ?? ""}
            onChange={(e) => onChange({ ...value, ar: e.target.value })}
            className="w-full rounded-md border border-ink-900/15 px-3 py-2 text-end font-sans text-sm focus:border-moss-500 focus:outline-none focus:ring-2 focus:ring-moss-500/20"
          />
        </div>
      </div>
    </div>
  );
}
