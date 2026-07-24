import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        moss: {
          50: "#F1F4EE", 100: "#DEE6D6", 300: "#A8BC94",
          500: "#65803F", 600: "#4A5D3A", 700: "#3A4A2E", 900: "#2A3520",
        },
        ochre: {
          50: "#FAF3E7", 100: "#F0DFB8", 400: "#D3A354", 500: "#C08A3E", 600: "#A6712D",
        },
        indigo: {
          700: "#2E3A56", 800: "#28324A", 900: "#232C42", 950: "#1A2033",
        },
        sand: { 50: "#FAF7F1", 100: "#F3EDE1" },
        ink: { 700: "#4A473F", 800: "#33312A", 900: "#24221D" },
        terracotta: { 500: "#C15A4E", 600: "#B54A3F" },
        sage: { 500: "#3F7D4F", 600: "#356A42" },
      },
      fontFamily: {
        display: ["Manrope", "Tajawal", "system-ui", "sans-serif"],
        sans: ["Inter", "Tajawal", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      borderRadius: {
        lg: "0.625rem",
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
