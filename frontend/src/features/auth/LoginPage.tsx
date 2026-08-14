/**
 * Écran de connexion. Utilise exclusivement des classes Tailwind logiques
 * (ps-, pe-, text-start...) pour rester correct visuellement en arabe (RTL).
 * Seul écran de l'application à utiliser le motif signature (ZelligePattern).
 */
import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Navigate } from "react-router-dom";

import { Logo } from "../../shared/ui/Logo";
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
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-ochre-500 text-indigo-950 shadow-lift">
            <Logo className="h-6 w-6" />
          </div>
          <h1 className="font-display text-2xl font-extrabold tracking-tight text-white">{t("app.name")}</h1>
          <p className="mt-1 font-mono text-[11px] uppercase tracking-eyebrow text-ochre-400/80">
            ERP · coopératives marocaines
          </p>
        </div>

        <form onSubmit={handleSubmit} className="overflow-hidden rounded-lg border border-white/10 bg-white shadow-lift">
          <div className="h-1.5 bg-gradient-to-r from-moss-600 via-ochre-500 to-terracotta-500" aria-hidden="true" />

          <div className="p-8">
            <label className="field-label" htmlFor="email">
              {t("auth.email")}
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input mb-4"
              autoComplete="email"
            />

            <label className="field-label" htmlFor="password">
              {t("auth.password")}
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input mb-4"
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
              className="w-full rounded-md bg-moss-700 py-2.5 text-sm font-semibold text-white transition hover:bg-moss-800 focus:outline-none focus:ring-2 focus:ring-moss-600/40 disabled:opacity-50"
            >
              {isLoading ? t("common.loading") : t("auth.login")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
