import { useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "../../shared/ui/Button";
import { SelectField, TextField } from "../../shared/ui/FormField";
import { createInvitation } from "./api";
import { ROLE_OPTIONS, type Invitation, type UserRole } from "./types";

interface Props {
  onClose: () => void;
  onCreated: (invitation: Invitation) => void;
}

export function InviteMemberModal({ onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<UserRole>("staff");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);
    try {
      const invitation = await createInvitation({ email, role });
      onCreated(invitation);
      onClose();
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error
          ?.message ?? t("common.error_generic");
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/40 px-4">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="font-display text-lg font-bold text-ink-900">{t("team.invite_title")}</h2>
        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <TextField
            id="invite-email"
            type="email"
            label={t("team.field.email")}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <SelectField
            id="invite-role"
            label={t("team.field.role")}
            value={role}
            onChange={(e) => setRole(e.target.value as UserRole)}
          >
            {ROLE_OPTIONS.map((r) => (
              <option key={r} value={r}>
                {t(`roles.${r}`)}
              </option>
            ))}
          </SelectField>

          {error && <p className="text-start text-sm text-terracotta-600">{error}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={onClose}>
              {t("common.cancel")}
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {t("team.send_invite")}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
