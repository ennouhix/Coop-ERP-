/**
 * Écran de connexion. Utilise exclusivement des classes Tailwind logiques
 * (ps-, pe-, text-start...) pour rester correct visuellement en arabe (RTL).
 * Seul écran de l'application à utiliser le motif signature (ZelligePattern).
 */
import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Navigate } from "react-router-dom";

import { ZelligePattern } from "../../shared/ui/ZelligePattern";
import { useAuthStore } from "./authStore";

export function LoginPage() {
  const { t } = useTranslation();
  const { login, isLoading, error, isAuthenticated } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      await login(email, password);
    } catch {
      // L'erreur est déjà exposée via le store (état `error`).
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-indigo-950 px-4">
      <ZelligePattern className="pointer-events-none absolute inset-0 h-full w-full text-ochre-500/10" />

      <div className="relative w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-lg bg-ochre-500 font-display text-lg font-extrabold text-indigo-950">
            C
          </div>
          <h1 className="font-display text-xl font-bold text-white">{t("app.name")}</h1>
        </div>

        <form onSubmit={handleSubmit} className="rounded-lg bg-white p-8 shadow-xl">
          <label className="mb-1 block text-start text-sm font-medium text-ink-800">
            {t("auth.email")}
          </label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mb-4 w-full rounded-md border border-ink-900/15 px-3 py-2 text-start text-sm focus:border-moss-500 focus:outline-none focus:ring-2 focus:ring-moss-500/20"
            autoComplete="email"
          />

          <label className="mb-1 block text-start text-sm font-medium text-ink-800">
            {t("auth.password")}
          </label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mb-4 w-full rounded-md border border-ink-900/15 px-3 py-2 text-start text-sm focus:border-moss-500 focus:outline-none focus:ring-2 focus:ring-moss-500/20"
            autoComplete="current-password"
          />

          {error && (
            <p role="alert" className="mb-4 text-start text-sm text-terracotta-600">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-md bg-moss-600 py-2.5 text-sm font-semibold text-white transition hover:bg-moss-700 focus:outline-none focus:ring-2 focus:ring-moss-500/40 disabled:opacity-50"
          >
            {isLoading ? t("common.loading") : t("auth.login")}
          </button>
        </form>
      </div>
    </div>
  );
}
