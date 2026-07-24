import {
  LayoutDashboard, Users, Handshake, Package, Warehouse,
  ArrowLeftRight, ShoppingCart, TrendingUp, Receipt, FileBarChart, Settings, UserCog,
} from "lucide-react";
import type { ComponentType } from "react";

export interface NavItem {
  to: string;
  labelKey: string;
  icon: ComponentType<{ className?: string }>;
  /** Modules pas encore livrés : affichés grisés avec un badge "Bientôt". */
  comingSoon?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { to: "/dashboard", labelKey: "nav.dashboard", icon: LayoutDashboard },
  { to: "/members", labelKey: "nav.members", icon: Users },
  { to: "/partners", labelKey: "nav.partners", icon: Handshake },
  { to: "/catalog", labelKey: "nav.catalog", icon: Package },
  { to: "/warehouses", labelKey: "nav.warehouses", icon: Warehouse },
  { to: "/inventory", labelKey: "nav.inventory", icon: ArrowLeftRight },
  { to: "/purchases", labelKey: "nav.purchases", icon: ShoppingCart },
  { to: "/sales", labelKey: "nav.sales", icon: TrendingUp },
  { to: "/billing", labelKey: "nav.billing", icon: Receipt },
  { to: "/reports", labelKey: "nav.reports", icon: FileBarChart, comingSoon: true },
  { to: "/team", labelKey: "nav.team", icon: UserCog },
  { to: "/settings", labelKey: "nav.settings", icon: Settings },
];
