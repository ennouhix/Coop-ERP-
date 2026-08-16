import {
  LayoutDashboard, Users, Handshake, Package, Warehouse, Coins, Landmark, HandCoins,
  ArrowLeftRight, ShoppingCart, TrendingUp, Receipt, FileBarChart, Settings, UserCog, ShieldCheck, FileText,
} from "lucide-react";
import type { ComponentType } from "react";

export interface NavItem {
  to: string;
  labelKey: string;
  icon: ComponentType<{ className?: string }>;
  /** Libellé de section i18n (nav.section.*) — regroupe les entrées du menu. */
  section: string;
  /** Module RBAC requis pour voir cette entrée. Absent = visible par tous. */
  module?: string;
  /** Modules pas encore livrés : affichés grisés avec un badge "Bientôt". */
  comingSoon?: boolean;
}

export const NAV_SECTIONS = ["pilotage", "commerce", "administration", "config"] as const;

export const NAV_ITEMS: NavItem[] = [
  { to: "/dashboard", labelKey: "nav.dashboard", icon: LayoutDashboard, section: "pilotage" },
  { to: "/reports", labelKey: "nav.reports", icon: FileBarChart, section: "pilotage", module: "reports" },
  { to: "/members", labelKey: "nav.members", icon: Users, section: "commerce", module: "members" },
  { to: "/shares", labelKey: "nav.shares", icon: Coins, section: "commerce", module: "members" },
  { to: "/contributions", labelKey: "nav.contributions", icon: HandCoins, section: "commerce", module: "contributions" },
  { to: "/partners", labelKey: "nav.partners", icon: Handshake, section: "commerce", module: "partners" },
  { to: "/catalog", labelKey: "nav.catalog", icon: Package, section: "commerce", module: "catalog" },
  { to: "/warehouses", labelKey: "nav.warehouses", icon: Warehouse, section: "commerce", module: "warehouses" },
  { to: "/inventory", labelKey: "nav.inventory", icon: ArrowLeftRight, section: "commerce", module: "stock" },
  { to: "/purchases", labelKey: "nav.purchases", icon: ShoppingCart, section: "commerce", module: "purchases" },
  { to: "/sales", labelKey: "nav.sales", icon: TrendingUp, section: "commerce", module: "sales" },
  { to: "/billing", labelKey: "nav.billing", icon: Receipt, section: "commerce", module: "billing" },
  { to: "/accounting", labelKey: "nav.accounting", icon: FileBarChart, section: "administration", module: "accounting" },
  { to: "/assemblies", labelKey: "nav.assemblies", icon: Landmark, section: "administration", module: "assemblies" },
  { to: "/documents", labelKey: "nav.documents", icon: FileText, section: "administration", module: "documents" },
  { to: "/team", labelKey: "nav.team", icon: UserCog, section: "administration", module: "users" },
  { to: "/roles", labelKey: "nav.roles_permissions", icon: ShieldCheck, section: "administration", module: "users" },
  { to: "/settings", labelKey: "nav.settings", icon: Settings, section: "config", module: "settings" },
];
