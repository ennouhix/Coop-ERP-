import { Mail, UserPlus, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { useAuthStore } from "../auth/authStore";
import { Button } from "../../shared/ui/Button";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import {
  cancelInvitation,
  changeUserRole,
  deactivateUser,
  listInvitations,
  listTeamMembers,
  reactivateUser,
} from "./api";
import { InviteMemberModal } from "./InviteMemberModal";
import { ROLE_OPTIONS, type Invitation, type TeamMember, type UserRole } from "./types";

export function TeamListPage() {
  const { t } = useTranslation();
  const currentUser = useAuthStore((state) => state.user);
  const canManage = currentUser?.role === "owner" || currentUser?.role === "admin";

  const [members, setMembers] = useState<TeamMember[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);

  function reload() {
    setIsLoading(true);
    Promise.all([listTeamMembers(), canManage ? listInvitations() : Promise.resolve([])])
      .then(([m, inv]) => {
        setMembers(m);
        setInvitations(inv);
      })
      .finally(() => setIsLoading(false));
  }

  useEffect(reload, [canManage]);

  async function handleRoleChange(userId: string, role: UserRole) {
    setBusyId(userId);
    try {
      const updated = await changeUserRole(userId, role);
      setMembers((prev) => prev.map((m) => (m.id === userId ? updated : m)));
    } finally {
      setBusyId(null);
    }
  }

  async function handleToggleActive(member: TeamMember) {
    setBusyId(member.id);
    try {
      if (member.is_active) {
        await deactivateUser(member.id);
        setMembers((prev) => prev.map((m) => (m.id === member.id ? { ...m, is_active: false } : m)));
      } else {
        const updated = await reactivateUser(member.id);
        setMembers((prev) => prev.map((m) => (m.id === member.id ? updated : m)));
      }
    } finally {
      setBusyId(null);
    }
  }

  async function handleCancelInvitation(id: string) {
    setBusyId(id);
    try {
      await cancelInvitation(id);
      setInvitations((prev) => prev.filter((i) => i.id !== id));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">{t("team.title")}</h1>
          <p className="page-heading-subtitle">{t("team.count", { count: members.length })}</p>
        </div>
        {canManage && (
          <Button onClick={() => setShowInviteModal(true)}>
            <UserPlus className="h-4 w-4" />
            {t("team.invite")}
          </Button>
        )}
      </div>

      <div className="mt-6 card">
        <table className="w-full text-start text-sm">
          <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
            <tr>
              <th className="px-4 py-3 text-start">{t("team.field.name")}</th>
              <th className="px-4 py-3 text-start">{t("team.field.email")}</th>
              <th className="px-4 py-3 text-start">{t("team.field.role")}</th>
              <th className="px-4 py-3 text-start">{t("team.field.status")}</th>
              {canManage && <th className="px-4 py-3 text-start">{t("common.edit")}</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-900/5">
            {isLoading && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-ink-700">
                  {t("common.loading")}
                </td>
              </tr>
            )}
            {!isLoading &&
              members.map((member) => {
                const isSelf = member.id === currentUser?.id;
                const isOwner = member.role === "owner";
                return (
                  <tr key={member.id} className="hover:bg-sand-50">
                    <td className="px-4 py-3 font-medium text-ink-900">
                      {member.first_name} {member.last_name}
                      {isSelf && <span className="ms-1.5 text-xs text-ink-700/60">{t("team.you")}</span>}
                    </td>
                    <td className="px-4 py-3 text-ink-700">{member.email}</td>
                    <td className="px-4 py-3">
                      {canManage && !isOwner && !isSelf ? (
                        <select
                          value={member.role}
                          disabled={busyId === member.id}
                          onChange={(e) => handleRoleChange(member.id, e.target.value as UserRole)}
                          className="input-inline px-2 py-1"
                        >
                          {ROLE_OPTIONS.map((r) => (
                            <option key={r} value={r}>
                              {t(`roles.${r}`)}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <StatusBadge label={t(`roles.${member.role}`)} tone={isOwner ? "ochre" : "neutral"} />
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge
                        label={t(member.is_active ? "team.status_active" : "team.status_inactive")}
                        tone={member.is_active ? "moss" : "neutral"}
                      />
                    </td>
                    {canManage && (
                      <td className="px-4 py-3">
                        {!isOwner && !isSelf && (
                          <Button
                            variant={member.is_active ? "danger" : "secondary"}
                            className="px-2.5 py-1 text-xs"
                            disabled={busyId === member.id}
                            onClick={() => handleToggleActive(member)}
                          >
                            {t(member.is_active ? "team.deactivate" : "team.reactivate")}
                          </Button>
                        )}
                      </td>
                    )}
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>

      {canManage && invitations.length > 0 && (
        <div className="mt-8">
          <h2 className="font-display text-lg font-bold text-ink-900">{t("team.pending_invitations")}</h2>
          <div className="mt-3 card">
            <table className="w-full text-start text-sm">
              <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
                <tr>
                  <th className="px-4 py-3 text-start">{t("team.field.email")}</th>
                  <th className="px-4 py-3 text-start">{t("team.field.role")}</th>
                  <th className="px-4 py-3 text-start">{t("team.field.expires_at")}</th>
                  <th className="px-4 py-3 text-start"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-900/5">
                {invitations.map((inv) => (
                  <tr key={inv.id} className="hover:bg-sand-50">
                    <td className="px-4 py-3 text-ink-700">
                      <Mail className="me-1.5 inline h-3.5 w-3.5 text-ink-700/50" />
                      {inv.email}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge label={t(`roles.${inv.role}`)} tone="neutral" />
                    </td>
                    <td className="px-4 py-3 text-ink-700">{inv.expires_at.slice(0, 10)}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleCancelInvitation(inv.id)}
                        disabled={busyId === inv.id}
                        className="inline-flex items-center gap-1 text-xs text-terracotta-600 hover:underline"
                      >
                        <X className="h-3.5 w-3.5" />
                        {t("team.cancel_invitation")}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showInviteModal && (
        <InviteMemberModal
          onClose={() => setShowInviteModal(false)}
          onCreated={(inv) => setInvitations((prev) => [inv, ...prev])}
        />
      )}
    </div>
  );
}
