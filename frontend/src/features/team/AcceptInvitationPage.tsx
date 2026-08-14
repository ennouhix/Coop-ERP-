import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearchParams } from "react-router-dom";

import { apiClient, setTokens } from "../../api/client";
import { Button } from "../../shared/ui/Button";
import { TextField } from "../../shared/ui/FormField";
import { useAuthStore } from "../auth/authStore";
import { acceptInvitation } from "./api";

export function AcceptInvitationPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      const data = (await acceptInvitation({
        token,
        first_name: firstName,
        last_name: lastName,
        password,
      })) as { access: string; refresh: string; user: Record<string, unknown> };

      setTokens({ access: data.access, refresh: data.refresh });
      apiClient.defaults.headers.common.Authorization = `Bearer ${data.access}`;
      useAuthStore.setState({
        user: data.user as never,
        isAuthenticated: true,
      });
      navigate("/dashboard", { replace: true });
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error
          ?.message ?? t("common.error_generic");
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-sand-50">
        <p className="text-ink-700">{t("team.invalid_invitation_link")}</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-sand-50 px-4">
      <div className="w-full max-w-md card card-pad">
        <h1 className="page-title">{t("team.accept_title")}</h1>
        <p className="page-heading-subtitle">{t("team.accept_subtitle")}</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <TextField
            id="accept-first-name"
            label={t("team.field.first_name")}
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            required
          />
          <TextField
            id="accept-last-name"
            label={t("team.field.last_name")}
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            required
          />
          <TextField
            id="accept-password"
            type="password"
            label={t("team.field.password")}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {error && <p className="text-start text-sm text-terracotta-600">{error}</p>}

          <Button type="submit" className="w-full justify-center" disabled={isSubmitting}>
            {t("team.accept_submit")}
          </Button>
        </form>
      </div>
    </div>
  );
}
