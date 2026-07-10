import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import ar from "./locales/ar/common.json";
import fr from "./locales/fr/common.json";

export const RTL_LANGUAGES = ["ar"] as const;

i18n.use(initReactI18next).init({
  resources: {
    fr: { common: fr },
    ar: { common: ar },
  },
  lng: "fr",
  fallbackLng: "fr",
  defaultNS: "common",
  interpolation: { escapeValue: false },
});

export default i18n;
