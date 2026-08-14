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
      <span className="field-label">
        {label} {required && <span className="text-terracotta-600">*</span>}
      </span>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-start text-xs text-ink-600">{t("catalog.lang_fr")}</label>
          <Tag
            required={required}
            rows={multiline ? 2 : undefined}
            value={value.fr}
            onChange={(e) => onChange({ ...value, fr: e.target.value })}
            className="input"
          />
        </div>
        <div>
          <label className="mb-1 block text-start text-xs text-ink-600">{t("catalog.lang_ar")}</label>
          <Tag
            rows={multiline ? 2 : undefined}
            dir="rtl"
            value={value.ar ?? ""}
            onChange={(e) => onChange({ ...value, ar: e.target.value })}
            className="input text-end font-sans"
          />
        </div>
      </div>
    </div>
  );
}
