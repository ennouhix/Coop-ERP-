import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { apiClient, setTokens } from "../../api/client";
import { Logo } from "../../shared/ui/Logo";
import { ZelligePattern } from "../../shared/ui/ZelligePattern";
import { activatePortalAccount } from "./api";
import { useAuthStore } from "./authStore";

export function ActivateAccountPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    (async () => {
      try {
        const data = await activatePortalAccount(token);
        if (cancelled) return;
        setTokens({ access: data.access, refresh: data.refresh });
        apiClient.defaults.headers.common.Authorization = `Bearer ${data.access}`;
        useAuthStore.setState({ user: data.user as never, isAuthenticated: true });
        navigate("/dashboard", { replace: true });
      } catch (err: unknown) {
        if (cancelled) return;
        const message =
          (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data
            ?.error?.message ?? t("common.error_generic");
        setError(message);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [token, navigate, t]);

  if (!token) {
    return (
      <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-indigo-950 px-4">
        <ZelligePattern className="pointer-events-none absolute inset-0 h-full w-full text-ochre-500/10" />
        <p className="relative text-sm text-indigo-200">{t("auth.activate.invalid_link")}</p>
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-indigo-950 px-4">
      <ZelligePattern className="pointer-events-none absolute inset-0 h-full w-full text-ochre-500/10" />

      <div className="relative w-full max-w-md text-center">
        <div className="mx-auto mb-6 flex h-12 w-12 items-center justify-center rounded-lg bg-moss-700 text-white shadow-lift">
          <Logo className="h-6 w-6" />
        </div>

        {error ? (
          <>
            <h1 className="font-display text-2xl font-extrabold tracking-tight text-white">
              {t("auth.activate.error_title")}
            </h1>
            <p role="alert" className="mt-3 text-sm leading-relaxed text-terracotta-300">
              {error}
            </p>
            <Link
              to="/login"
              className="mt-8 inline-block text-sm font-semibold text-ochre-400 hover:text-ochre-300"
            >
              {t("auth.register.back_to_login")}
            </Link>
          </>
        ) : (
          <>
            <h1 className="font-display text-2xl font-extrabold tracking-tight text-white">
              {t("auth.activate.processing_title")}
            </h1>
            <p className="mt-3 text-sm text-indigo-200">{t("common.loading")}</p>
          </>
        )}
      </div>
    </div>
  );
}
