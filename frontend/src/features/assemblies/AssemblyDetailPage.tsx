import { ArrowLeft, CheckCheck, UserPlus } from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";

import { extractApiErrorMessage } from "../../shared/api/errors";
import { Button } from "../../shared/ui/Button";
import { SelectField } from "../../shared/ui/FormField";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { listMembers } from "../members/api";
import type { Member } from "../members/types";
import {
  getAssembly,
  listAssemblyAttendances,
  registerAttendance,
  updateAssembly,
} from "./api";
import type {
  Assembly,
  AssemblyAttendance,
  AssemblyStatus,
  AttendanceFormValues,
} from "./types";
import { EMPTY_ATTENDANCE_FORM } from "./types";

const STATUS_TONE: Record<AssemblyStatus, "moss" | "ochre" | "neutral" | "terracotta"> = {
  draft: "neutral",
  scheduled: "ochre",
  done: "moss",
  cancelled: "terracotta",
};

const ATTENDANCE_TONE: Record<string, "moss" | "terracotta" | "neutral" | "ochre"> = {
  present: "moss",
  absent: "terracotta",
  excused: "ochre",
};

export function AssemblyDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();

  const [assembly, setAssembly] = useState<Assembly | null>(null);
  const [attendances, setAttendances] = useState<AssemblyAttendance[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [attendance, setAttendance] = useState<AttendanceFormValues>(EMPTY_ATTENDANCE_FORM);
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingAttendance, setIsSavingAttendance] = useState(false);
  const [isMarkingDone, setIsMarkingDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function refreshAttendanceData() {
    if (!id) return;
    listAssemblyAttendances(id).then((data) => setAttendances(data.results));
    getAssembly(id).then(setAssembly);
  }

  useEffect(() => {
    if (!id) return;
    setIsLoading(true);
    getAssembly(id)
      .then(setAssembly)
      .finally(() => setIsLoading(false));
    listAssemblyAttendances(id).then((data) => setAttendances(data.results));
    listMembers({}).then((data) => setMembers(data.results));
  }, [id]);

  async function handleRegisterAttendance(event: FormEvent) {
    event.preventDefault();
    if (!id || !attendance.member_id) return;
    setError(null);
    setIsSavingAttendance(true);
    try {
      await registerAttendance(id, attendance);
      setAttendance(EMPTY_ATTENDANCE_FORM);
      refreshAttendanceData();
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsSavingAttendance(false);
    }
  }

  async function handleMarkDone() {
    if (!assembly) return;
    setError(null);
    setIsMarkingDone(true);
    try {
      setAssembly(await updateAssembly(assembly.id, { status: "done" }));
    } catch (err) {
      setError(extractApiErrorMessage(err, t("common.error_generic")));
    } finally {
      setIsMarkingDone(false);
    }
  }

  if (isLoading) return <p className="text-sm text-ink-700">{t("common.loading")}</p>;
  if (!assembly) return <p className="text-sm text-terracotta-600">{t("assemblies.not_found")}</p>;

  const canMarkDone = assembly.status === "draft" || assembly.status === "scheduled";

  return (
    <div className="mx-auto max-w-3xl">
      <Link to="/assemblies" className="inline-flex items-center gap-1.5 text-sm text-ink-700 hover:text-ink-900">
        <ArrowLeft className="h-4 w-4" />
        {t("assemblies.back_to_list")}
      </Link>

      <div className="mt-3 flex items-center justify-between">
        <div>
          <p className="font-mono text-xs text-ink-700/70">{t("assemblies.field.scheduled_date")} · {assembly.scheduled_date}</p>
          <h1 className="page-title">{assembly.title}</h1>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge label={t(`assemblies.status_${assembly.status}`)} tone={STATUS_TONE[assembly.status]} />
          {canMarkDone && (
            <Button onClick={handleMarkDone} disabled={isMarkingDone}>
              <CheckCheck className="h-4 w-4" />
              {t("assemblies.mark_done")}
            </Button>
          )}
        </div>
      </div>

      {error && <p role="alert" className="mt-3 text-start text-sm text-terracotta-600">{error}</p>}

      <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
        <div>
          <span className="text-ink-700/70">{t("assemblies.field.assembly_type")} : </span>
          <span className="text-ink-900">
            {t(assembly.assembly_type === "ordinary" ? "assemblies.type_ordinary" : "assemblies.type_extraordinary")}
          </span>
        </div>
        {assembly.location && (
          <div>
            <span className="text-ink-700/70">{t("assemblies.field.location")} : </span>
            <span className="text-ink-900">{assembly.location}</span>
          </div>
        )}
        <div>
          <span className="text-ink-700/70">{t("assemblies.field.quorum_percent")} : </span>
          <span className="font-semibold text-ink-900">{Number(assembly.quorum_percent).toLocaleString("fr-MA")} %</span>
        </div>
        <div>
          <span className="text-ink-700/70">{t("assemblies.field.presence")} : </span>
          <span className="font-semibold text-ink-900">
            {assembly.present_count} / {assembly.attendances_count}
          </span>
        </div>
      </div>

      {assembly.agenda && (
        <p className="mt-4 text-sm text-ink-700">
          <span className="font-medium">{t("assemblies.field.agenda")} : </span>
          {assembly.agenda}
        </p>
      )}

      {assembly.status !== "cancelled" && (
        <>
          <h2 className="mt-8 text-base font-semibold text-ink-900">{t("assemblies.register_attendance")}</h2>
          <form onSubmit={handleRegisterAttendance} className="mt-3 grid grid-cols-3 gap-3 card card-pad">
            <SelectField
              id="attendance_member" label={t("assemblies.field.member")} required
              value={attendance.member_id}
              onChange={(e) => setAttendance((prev) => ({ ...prev, member_id: e.target.value }))}
            >
              <option value="">{t("assemblies.select_member")}</option>
              {members.map((member) => (
                <option key={member.id} value={member.id}>
                  {member.member_number} — {member.full_name}
                </option>
              ))}
            </SelectField>
            <SelectField
              id="attendance_status" label={t("assemblies.field.attendance_status")}
              value={attendance.attendance_status}
              onChange={(e) =>
                setAttendance((prev) => ({
                  ...prev,
                  attendance_status: e.target.value as AttendanceFormValues["attendance_status"],
                }))
              }
            >
              <option value="present">{t("assemblies.attendance_present")}</option>
              <option value="absent">{t("assemblies.attendance_absent")}</option>
              <option value="excused">{t("assemblies.attendance_excused")}</option>
            </SelectField>
            <SelectField
              id="attendance_vote" label={t("assemblies.field.vote")}
              value={attendance.vote}
              onChange={(e) =>
                setAttendance((prev) => ({
                  ...prev,
                  vote: e.target.value as AttendanceFormValues["vote"],
                }))
              }
            >
              <option value="">{t("assemblies.vote_none")}</option>
              <option value="for">{t("assemblies.vote_for")}</option>
              <option value="against">{t("assemblies.vote_against")}</option>
              <option value="abstention">{t("assemblies.vote_abstention")}</option>
            </SelectField>
            <div className="col-span-3 flex justify-end pt-1">
              <Button type="submit" disabled={isSavingAttendance || !attendance.member_id}>
                {isSavingAttendance ? (
                  t("common.loading")
                ) : (
                  <>
                    <UserPlus className="h-4 w-4" />
                    {t("assemblies.register_button")}
                  </>
                )}
              </Button>
            </div>
          </form>

          <div className="mt-6 card">
            <table className="w-full text-start text-sm">
              <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
                <tr>
                  <th className="px-4 py-3 text-start">{t("assemblies.field.member_number")}</th>
                  <th className="px-4 py-3 text-start">{t("assemblies.field.member")}</th>
                  <th className="px-4 py-3 text-start">{t("assemblies.field.attendance_status")}</th>
                  <th className="px-4 py-3 text-start">{t("assemblies.field.vote")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-900/5">
                {attendances.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-ink-700">
                      {t("assemblies.attendance_empty")}
                    </td>
                  </tr>
                )}
                {attendances.map((att) => (
                  <tr key={att.id}>
                    <td className="px-4 py-3 font-mono text-xs text-ink-700">{att.member_number}</td>
                    <td className="px-4 py-3 font-medium text-ink-900">{att.member_name}</td>
                    <td className="px-4 py-3">
                      <StatusBadge
                        label={t(`assemblies.attendance_${att.attendance_status}`)}
                        tone={ATTENDANCE_TONE[att.attendance_status]}
                      />
                    </td>
                    <td className="px-4 py-3 text-ink-700">
                      {att.vote ? t(`assemblies.vote_${att.vote}`) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
