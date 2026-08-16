import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Logo } from "../../shared/ui/Logo";
import { ZelligePattern } from "../../shared/ui/ZelligePattern";
import { Button } from "../../shared/ui/Button";
import { TextField } from "../../shared/ui/FormField";
import { registerPortalAccount } from "./api";

function extractErrorMessage(err: unknown, fallback: string): string {
  const data = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
  if (data && typeof data === "object") {
    for (const value of Object.values(data)) {
      if (Array.isArray(value) && typeof value[0] === "string") {
        return value[0];
      }
    }
  }
  return fallback;
}

export function RegisterPage() {
  const { t } = useTranslation();
  const [cooperativeName, setCooperativeName] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedEmail, setSubmittedEmail] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (password !== confirmPassword) {
      setError(t("auth.register.password_mismatch"));
      return;
    }
    setIsSubmitting(true);
    try {
      await registerPortalAccount({
        cooperative_name: cooperativeName,
        owner_first_name: firstName,
        owner_last_name: lastName,
        owner_email: email,
        owner_password: password,
      });
      setSubmittedEmail(email);
    } catch (err: unknown) {
      setError(extractErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSubmitting(false);
    }
  }

  if (submittedEmail) {
    return (
      <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-indigo-950 px-4">
        <ZelligePattern className="pointer-events-none absolute inset-0 h-full w-full text-ochre-500/10" />
        <div className="relative w-full max-w-md text-center">
          <div className="mx-auto mb-6 flex h-12 w-12 items-center justify-center rounded-lg bg-moss-700 text-white shadow-lift">
            <Logo className="h-6 w-6" />
          </div>
          <h1 className="font-display text-2xl font-extrabold tracking-tight text-white">
            {t("auth.register.check_email_title")}
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-indigo-200">
            {t("auth.register.check_email_subtitle")}
          </p>
          <p className="mt-3 font-mono text-xs text-ochre-400/90">{submittedEmail}</p>
          <Link
            to="/login"
            className="mt-8 inline-block text-sm font-semibold text-ochre-400 hover:text-ochre-300"
          >
            {t("auth.register.back_to_login")}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-indigo-950 px-4 py-10">
      <ZelligePattern className="pointer-events-none absolute inset-0 h-full w-full text-ochre-500/10" />

      <div className="relative w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-ochre-500 text-indigo-950 shadow-lift">
            <Logo className="h-6 w-6" />
          </div>
          <h1 className="font-display text-2xl font-extrabold tracking-tight text-white">
            {t("auth.register_title")}
          </h1>
          <p className="mt-1 font-mono text-[11px] uppercase tracking-eyebrow text-ochre-400/80">
            {t("auth.register_subtitle")}
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="overflow-hidden rounded-lg border border-white/10 bg-white shadow-lift"
        >
          <div
            className="h-1.5 bg-gradient-to-r from-moss-600 via-ochre-500 to-terracotta-500"
            aria-hidden="true"
          />

          <div className="space-y-4 p-8">
            <TextField
              id="register-cooperative-name"
              label={t("auth.field.cooperative_name")}
              value={cooperativeName}
              onChange={(e) => setCooperativeName(e.target.value)}
              required
              minLength={2}
              autoComplete="organization"
            />

            <div className="grid gap-4 sm:grid-cols-2">
              <TextField
                id="register-first-name"
                label={t("auth.field.first_name")}
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                required
                autoComplete="given-name"
              />
              <TextField
                id="register-last-name"
                label={t("auth.field.last_name")}
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                required
                autoComplete="family-name"
              />
            </div>

            <TextField
              id="register-email"
              type="email"
              label={t("auth.field.email")}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />

            <TextField
              id="register-password"
              type="password"
              label={t("auth.field.password")}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
            />

            <TextField
              id="register-confirm-password"
              type="password"
              label={t("auth.field.confirm_password")}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={8}
              autoComplete="new-password"
            />

            {error && (
              <p role="alert" className="text-start text-sm text-terracotta-600">
                {error}
              </p>
            )}

            <Button type="submit" className="w-full justify-center" disabled={isSubmitting}>
              {isSubmitting ? t("common.loading") : t("auth.register_submit")}
            </Button>
          </div>
        </form>

        <p className="mt-6 text-center text-sm text-indigo-300">
          {t("auth.register.has_account")}{" "}
          <Link to="/login" className="font-semibold text-ochre-400 hover:text-ochre-300">
            {t("auth.login")}
          </Link>
        </p>
      </div>
    </div>
  );
}
