import type { Config } from "tailwindcss";

/* ------------------------------------------------------------------------
 * Identité « atelier » : une palette unique, tirée des terres et des
 * matières (argile, zellige, cuir, olive) — jamais de couleurs génériques
 * tailwind (slate/emerald/amber...) hors ce fichier.
 * ---------------------------------------------------------------------- */

const moss = {
  50: "#F4F6F0", 100: "#E6EBDD", 200: "#CED8BC", 300: "#A8BC94",
  400: "#8AA36E", 500: "#65803F", 600: "#4A5D3A", 700: "#3A4A2E",
  800: "#2F3B26", 900: "#2A3520", 950: "#1B2415",
};

const sage = {
  50: "#F0F6F1", 100: "#DCEBE0", 200: "#BAD7C4", 300: "#90BCA2",
  400: "#5FA080", 500: "#3F7D4F", 600: "#356A42", 700: "#2C5637",
  800: "#24462E", 900: "#1C3825", 950: "#11291A",
};

const ochre = {
  50: "#FBF6EA", 100: "#F5E7C9", 200: "#EDD29C", 300: "#E2BB6B",
  400: "#D3A354", 500: "#C08A3E", 600: "#A6712D", 700: "#875A25",
  800: "#6B471E", 900: "#543617", 950: "#3A240D",
};

const terracotta = {
  50: "#FBF1EF", 100: "#F5DCD7", 200: "#EBBAB2", 300: "#DD9187",
  400: "#CE6F63", 500: "#C15A4E", 600: "#B54A3F", 700: "#93392F",
  800: "#772E26", 900: "#5F251F", 950: "#401712",
};

const indigo = {
  50: "#EEF1F6", 100: "#DCE2EC", 200: "#BBC6D8", 300: "#93A3BF",
  400: "#687EA3", 500: "#4C6088", 600: "#3A4A6E", 700: "#2E3A56",
  800: "#28324A", 900: "#232C42", 950: "#1A2033",
};

const aubergine = {
  50: "#F5F0F4", 100: "#E9DCE6", 200: "#D4B9CF", 300: "#B790B0",
  400: "#96658C", 500: "#7A4A70", 600: "#663A5E", 700: "#532F4C",
  800: "#42263E", 900: "#351E32", 950: "#241325",
};

const sand = { 50: "#FAF7F1", 100: "#F3EDE1", 200: "#E9DFCC", 300: "#DCCFBE" };

const ink = {
  50: "#F8F6F2", 100: "#EFEBE3", 200: "#E0D9CB", 300: "#C9BFA9",
  400: "#A89C84", 500: "#887B64", 600: "#6B6150", 700: "#4A473F",
  800: "#33312A", 900: "#24221D", 950: "#171510",
};

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        moss,
        sage,
        ochre,
        terracotta,
        indigo,
        aubergine,
        sand,
        ink,
        /* Garde-fou : toute couleur générique qui resterait par erreur est
         * redirigée vers l'échelle de marque la plus proche — l'interface
         * reste toujours cohérente, jamais arc-en-ciel. */
        slate: ink,
        gray: ink,
        zinc: ink,
        neutral: ink,
        stone: ink,
        emerald: sage,
        green: sage,
        teal: sage,
        lime: sage,
        amber: ochre,
        yellow: ochre,
        orange: ochre,
        red: terracotta,
        rose: terracotta,
        pink: terracotta,
        blue: indigo,
        sky: indigo,
        cyan: indigo,
        purple: aubergine,
        violet: aubergine,
        fuchsia: aubergine,
      },
      fontFamily: {
        display: ["Manrope", "Tajawal", "system-ui", "sans-serif"],
        sans: ["Inter", "Tajawal", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      borderRadius: {
        lg: "0.625rem",
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(36 34 29 / 0.05)",
        lift: "0 6px 20px -6px rgb(36 34 29 / 0.14)",
        panel: "0 1px 0 0 rgb(36 34 29 / 0.04) inset, 0 1px 2px 0 rgb(36 34 29 / 0.05)",
      },
      letterSpacing: {
        eyebrow: "0.18em",
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
