// frontend/src/features/dashboard/DashboardPage.tsx

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { 
  TrendingUp, Users, Package, AlertTriangle, 
  BarChart3, PieChart as PieIcon, ArrowUpRight, ArrowDownRight 
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, PieChart, Pie, Cell
} from "recharts";
import { apiClient } from "../../api/client";
import { PageHeader } from "../../shared/ui/PageHeader";
import { StatusBadge } from "../../shared/ui/StatusBadge";

// Types pour les nouveaux graphiques
interface ChartData {
  date: string;
  revenue: number;
}

interface DashboardSummary {
  period: { date_from: string; date_to: string };
  members: { active_count: number; total_count: number };
  partners: { active_customers: number; active_suppliers: number };
  sales: {
    revenue_invoiced_period: string;
    orders_delivered: number;
  };
  stock: { total_stock_value: string; low_stock_lines_count: number };
  billing: { total_outstanding_balance: string; overdue_invoices_count: number };
}

// Données fictives pour l'évolution en attendant que l'API les fournisse
const MOCK_EVOLUTION: ChartData[] = [
  { date: "Jan", revenue: 45000 },
  { date: "Fév", revenue: 52000 },
  { date: "Mar", revenue: 48000 },
  { date: "Avr", revenue: 61000 },
  { date: "Mai", revenue: 55000 },
  { date: "Juin", revenue: 67000 },
];

const PARTNER_PIE = [
  { name: "Clients", value: 60, color: "#65803F" },
  { name: "Fournisseurs", value: 40, color: "#C08A3E" },
];

export function DashboardPage() {
  const { t, i18n } = useTranslation();
  const isRtl = i18n.dir() === "rtl";
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.get("/dashboard/summary/")
      .then((res) => setData(res.data))
      .catch((err) => console.error("Dashboard error", err))
      .finally(() => setLoading(false));
  }, []);

  const formatMAD = (val: string | number) => 
    new Intl.NumberFormat(i18n.language === 'ar' ? 'ar-MA' : 'fr-MA', {
      style: 'currency',
      currency: 'MAD',
      maximumFractionDigits: 0,
    }).format(Number(val));

  if (loading) return <div className="p-8 text-center text-ink-600">{t("common.loading")}</div>;
  if (!data) return <div className="p-8 text-terracotta-600">{t("dashboard.error")}</div>;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow={t("nav.section.pilotage")}
        title={t("nav.dashboard")}
        subtitle={t("dashboard.period", { from: data.period.date_from, to: data.period.date_to })}
      />

      {/* KPI Row */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard 
          title={t("dashboard.revenue")} 
          value={formatMAD(data.sales.revenue_invoiced_period)} 
          icon={<TrendingUp className="h-5 w-5" />}
          accent="text-sage-600 bg-sage-50 border-sage-200"
          trend="+12%"
          trendUp={true}
        />
        <KpiCard 
          title={t("dashboard.stock_value")} 
          value={formatMAD(data.stock.total_stock_value)} 
          icon={<Package className="h-5 w-5" />}
          accent="text-ochre-600 bg-ochre-50 border-ochre-200"
          alert={data.stock.low_stock_lines_count > 0 ? t("dashboard.low_stock") : undefined}
        />
        <KpiCard 
          title={t("dashboard.outstanding")} 
          value={formatMAD(data.billing.total_outstanding_balance)} 
          icon={<BarChart3 className="h-5 w-5" />}
          accent="text-indigo-600 bg-indigo-50 border-indigo-200"
        />
        <KpiCard 
          title={t("dashboard.active_members")} 
          value={data.members.active_count.toString()} 
          icon={<Users className="h-5 w-5" />}
          accent="text-aubergine-600 bg-aubergine-50 border-aubergine-200"
        />
      </div>

      {/* Main Charts Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        
        {/* Evolution Chart (Ventes) */}
        <div className="card lg:col-span-2">
          <div className="card-header">
            <h3>
              <span className="card-header-dot" />
              Évolution des Ventes (HT)
            </h3>
          </div>
          <div className="h-72 w-full p-5">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={MOCK_EVOLUTION} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#65803F" stopOpacity={0.16}/>
                    <stop offset="95%" stopColor="#65803F" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E9DFCC" />
                <XAxis 
                  dataKey="date" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fill: '#887B64', fontSize: 12 }} 
                  reversed={isRtl}
                />
                <YAxis hide={true} />
                <Tooltip 
                  contentStyle={{ borderRadius: 8, border: '1px solid #E0D9CB', boxShadow: '0 6px 20px -6px rgb(36 34 29 / 0.14)', fontSize: 13 }}
                  formatter={(val: number) => [formatMAD(val), "Ventes"]}
                />
                <Area 
                  type="monotone" 
                  dataKey="revenue" 
                  stroke="#65803F" 
                  strokeWidth={2.5}
                  fillOpacity={1} 
                  fill="url(#colorRev)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Alerts & Quick Status */}
        <div className="card">
          <div className="card-header">
            <h3>
              <span className="card-header-dot" />
              Alertes et Statuts
            </h3>
          </div>
          <div className="space-y-3 p-5">
            <AlertRow label="Produits en rupture" value={data.stock.low_stock_lines_count} tone={data.stock.low_stock_lines_count > 0 ? "terracotta" : "moss"} />
            <AlertRow label="Factures en retard" value={data.billing.overdue_invoices_count} tone={data.billing.overdue_invoices_count > 0 ? "ochre" : "moss"} />
            <AlertRow label="Livraisons terminées" value={data.sales.orders_delivered} tone="neutral" />
          </div>

          <div className="card-section">
            <p className="mb-4 font-mono text-[10px] font-medium uppercase tracking-eyebrow text-ink-600">
              Répartition Clients/Fournisseurs
            </p>
            <div className="h-32">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={PARTNER_PIE} dataKey="value" nameKey="name" innerRadius={30} outerRadius={48} paddingAngle={4} strokeWidth={2} stroke="#ffffff">
                    {PARTNER_PIE.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #E0D9CB', fontSize: 13 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-3 flex items-center justify-between">
              <div>
                <div className="text-xl font-bold text-ink-900">{data.partners.active_customers}</div>
                <div className="text-xs text-ink-600">Clients actifs</div>
              </div>
              <div className="h-10 w-px bg-ink-200" />
              <div className="text-end">
                <div className="text-xl font-bold text-ink-900">{data.partners.active_suppliers}</div>
                <div className="text-xs text-ink-600">Fournisseurs</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AlertRow({ label, value, tone }: { label: string; value: number; tone: "moss" | "ochre" | "terracotta" | "neutral" }) {
  return (
    <div className="flex items-center justify-between rounded-md border border-ink-900/5 bg-sand-50 px-3 py-2.5">
      <span className="text-sm text-ink-700">{label}</span>
      <StatusBadge label={String(value)} tone={tone} />
    </div>
  );
}

function KpiCard({ title, value, icon, accent, trend, trendUp, alert }: { 
  title: string; value: string; icon: React.ReactNode; accent: string; trend?: string; trendUp?: boolean; alert?: string 
}) {
  return (
    <div className="card p-5 transition-shadow hover:shadow-lift">
      <div className="flex items-start justify-between">
        <div className={`flex h-10 w-10 items-center justify-center rounded-md border ${accent}`}>{icon}</div>
        {trend && (
          <div className={`flex items-center text-xs font-medium ${trendUp ? 'text-sage-700' : 'text-terracotta-700'}`}>
            {trendUp ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
            {trend}
          </div>
        )}
      </div>
      <p className="mt-4 font-mono text-[10px] font-medium uppercase tracking-eyebrow text-ink-600">{title}</p>
      <div className="mt-1 font-display text-2xl font-extrabold tracking-tight text-ink-900">{value}</div>
      {alert && (
        <div className="mt-3">
          <StatusBadge label={alert} tone="terracotta" />
        </div>
      )}
    </div>
  );
}
