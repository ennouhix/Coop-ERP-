import { useTranslation } from "react-i18next";

import { StatusBadge } from "./StatusBadge";

const TONE_BY_STATUS: Record<string, "moss" | "ochre" | "terracotta" | "neutral"> = {
  draft: "neutral",
  confirmed: "ochre",
  partially_received: "ochre",
  partially_delivered: "ochre",
  received: "moss",
  delivered: "moss",
  cancelled: "terracotta",
};

/** Badge de statut de commande, réutilisé par Achats et Ventes (statuts nommés différemment mais même cycle). */
export function OrderStatusBadge({ status, i18nPrefix }: { status: string; i18nPrefix: string }) {
  const { t } = useTranslation();
  return <StatusBadge label={t(`${i18nPrefix}.status_${status}`)} tone={TONE_BY_STATUS[status] ?? "neutral"} />;
}
