import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "Tajawal", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
} satisfies Config;

/**
 * Règle d'équipe (à faire respecter en revue de code) :
 * interdiction d'utiliser ml-, mr-, pl-, pr-, text-left, text-right.
 * Utiliser exclusivement les classes logiques : ms-, me-, ps-, pe-,
 * text-start, text-end — indispensable pour que l'interface arabe (RTL)
 * ne soit jamais visuellement cassée.
 */
