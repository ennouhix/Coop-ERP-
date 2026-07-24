import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";

import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { TextareaField, TextField } from "../../shared/ui/FormField";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { deactivateMember, getMember, reactivateMember, updateMember } from "./api";
import type { Member, MemberStatus } from "./types";

const STATUS_TONE: Record<MemberStatus, "moss" | "ochre" | "neutral"> = {
  active: "moss",
  suspended: "ochre",
  inactive: "neutral",
};

export function MemberDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [member, setMember] = useState<Member | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getMember(id).then(setMember).finally(() => setIsLoading(false));
  }, [id]);

  function update<K extends keyof Member>(key: K, value: Member[K]) {
    setMember((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  async function handleSave() {
    if (!member) return;
    setError(null);
    setSuccessMessage(null);
    setIsSaving(true);
    try {
      const updated = await updateMember(member.id, {
        first_name: member.first_name, last_name: member.last_name,
        phone_number: member.phone_number, email: member.email,
        address: member.address, city: member.city,
        shares_count: member.shares_count, notes: member.notes,
      });
      setMember(updated);
      setSuccessMessage(t("common.saved"));
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleToggleStatus() {
    if (!member) return;
    setError(null);
    try {
      if (member.status === "inactive") {
        const updated = await reactivateMember(member.id);
        setMember(updated);
      } else {
        await deactivateMember(member.id);
        setMember({ ...member, status: "inactive" });
      }
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    }
  }

  if (isLoading) return <p className="text-sm text-ink-700">{t("common.loading")}</p>;
  if (!member) return <p className="text-sm text-terracotta-600">{t("members.not_found")}</p>;

  return (
    <div className="mx-auto max-w-2xl">
      <Link to="/members" className="inline-flex items-center gap-1.5 text-sm text-ink-700 hover:text-ink-900">
        <ArrowLeft className="h-4 w-4" />
        {t("members.back_to_list")}
      </Link>

      <div className="mt-3 flex items-center justify-between">
        <div>
          <p className="font-mono text-xs text-ink-700/70">{member.member_number}</p>
          <h1 className="font-display text-2xl font-bold text-ink-900">{member.full_name}</h1>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge label={t(`members.status_${member.status}`)} tone={STATUS_TONE[member.status]} />
          <Button
            variant={member.status === "inactive" ? "secondary" : "danger"}
            onClick={handleToggleStatus}
          >
            {member.status === "inactive" ? t("members.reactivate") : t("members.deactivate")}
          </Button>
        </div>
      </div>

      <div className="mt-6 space-y-4 rounded-lg border border-ink-900/5 bg-white p-6 shadow-sm">
        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="first_name" label={t("members.field.first_name")}
            value={member.first_name} onChange={(e) => update("first_name", e.target.value)}
          />
          <TextField
            id="last_name" label={t("members.field.last_name")}
            value={member.last_name} onChange={(e) => update("last_name", e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="phone_number" label={t("members.field.phone_number")}
            value={member.phone_number} onChange={(e) => update("phone_number", e.target.value)}
          />
          <TextField id="cin" label={t("members.field.cin")} value={member.cin} disabled />
        </div>

        <TextField
          id="email" type="email" label={t("members.field.email")}
          value={member.email} onChange={(e) => update("email", e.target.value)}
        />

        <div className="grid grid-cols-2 gap-4">
          <TextField
            id="address" label={t("members.field.address")}
            value={member.address} onChange={(e) => update("address", e.target.value)}
          />
          <TextField
            id="city" label={t("members.field.city")}
            value={member.city} onChange={(e) => update("city", e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <TextField id="join_date" label={t("members.field.join_date")} value={member.join_date} disabled />
          <TextField
            id="shares_count" type="number" min={0} label={t("members.field.shares_count")}
            value={member.shares_count} onChange={(e) => update("shares_count", Number(e.target.value))}
          />
        </div>

        <TextareaField
          id="notes" label={t("members.field.notes")}
          value={member.notes} onChange={(e) => update("notes", e.target.value)}
        />

        {error && <p role="alert" className="text-start text-sm text-terracotta-600">{error}</p>}
        {successMessage && <p className="text-start text-sm text-moss-600">{successMessage}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={() => navigate("/members")}>
            {t("common.cancel")}
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? t("common.loading") : t("common.save")}
          </Button>
        </div>
      </div>
    </div>
  );
}
