import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ArrowLeftRight,
  BookOpenText,
  ChevronDown,
  ChevronUp,
  Eye,
  EyeOff,
  FileDown,
  FileSpreadsheet,
  FileText,
  Handshake,
  Loader2,
  Package,
  ShoppingCart,
  Truck,
  Users,
  type LucideIcon,
} from "lucide-react";
import { PageHeader } from "../../shared/ui/PageHeader";
import { Button } from "../../shared/ui/Button";
import { ToastStack, type ToastItem } from "../../shared/ui/Toast";
import { listWarehouses } from "../warehouses/api";
import { listPartners } from "../partners/api";
import { listJournals } from "../accounting/api";
import {
  downloadReport,
  fetchReportPreview,
  type ReportFilters,
  type ReportOutput,
  type ReportPreview,
} from "./api";

interface FilterOption {
  value: string;
  label: string;
}

interface FilterDef {
  name: keyof ReportFilters;
  type: "date" | "month" | "select";
  label: string;
  options?: FilterOption[];
}

interface ReportDef {
  slug: string;
  stem: string;
  icon: LucideIcon;
  iconClass: string;
  title: string;
  desc: string;
  filters: FilterDef[];
}

interface CategoryDef {
  key: string;
  title: string;
  reports: ReportDef[];
}

const EMPTY_FILTERS: ReportFilters = {};

export function ReportsPage() {
  const { t } = useTranslation();

  const [filters, setFilters] = useState<Record<string, ReportFilters>>({});
  const [preview, setPreview] = useState<Record<string, ReportPreview | null>>({});
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [filtersOpen, setFiltersOpen] = useState<Record<string, boolean>>({});
  const [activeTab, setActiveTab] = useState("all");
  const [previewLoading, setPreviewLoading] = useState<Record<string, boolean>>({});
  const [downloading, setDownloading] = useState<Record<string, ReportOutput | null>>({});
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const toastId = useRef(0);

  // Options de filtres (chargées une seule fois).
  const [warehouses, setWarehouses] = useState<{ value: string; label: string }[]>([]);
  const [customers, setCustomers] = useState<{ value: string; label: string }[]>([]);
  const [suppliers, setSuppliers] = useState<{ value: string; label: string }[]>([]);
  const [journals, setJournals] = useState<{ value: string; label: string }[]>([]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const [wh, customersData, suppliersData, journalsData] = await Promise.all([
          listWarehouses(),
          listPartners({ is_customer: true, page: 1 }),
          listPartners({ is_supplier: true, page: 1 }),
          listJournals(),
        ]);
        if (cancelled) return;
        setWarehouses(wh.map((w) => ({ value: w.id, label: w.name })));
        setCustomers(customersData.results.map((p) => ({ value: p.id, label: p.name })));
        setSuppliers(suppliersData.results.map((p) => ({ value: p.id, label: p.name })));
        setJournals(journalsData.map((j) => ({ value: j.id, label: `${j.code} — ${j.name_display}` })));
      } catch (err) {
        console.error("Échec du chargement des options de filtres:", err);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const pushToast = (kind: "success" | "error", message: string) => {
    const id = ++toastId.current;
    setToasts((prev) => [...prev, { id, kind, message }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((item) => item.id !== id));
    }, 4000);
  };

  const statusOptions = (
    prefix: "sales" | "purchases" | "invoices",
    statuses: string[]
  ): FilterOption[] =>
    statuses.map((status) => ({
      value: status,
      label: t(`${prefix}.status_${status}`, status),
    }));

  const categories = useMemo<CategoryDef[]>(
    () => [
      {
        key: "members",
        title: t("reports.cat_members", "Adhérents & Partenaires"),
        reports: [
          {
            slug: "members",
            stem: "membres",
            icon: Users,
            iconClass: "bg-sage-100 text-sage-700",
            title: t("reports.members_title", "Adhérents & Membres"),
            desc: t(
              "reports.members_desc",
              "Liste exhaustive de tous les adhérents avec coordonnées, CIN, statut et parts sociales."
            ),
            filters: [],
          },
          {
            slug: "partners",
            stem: "partenaires",
            icon: Handshake,
            iconClass: "bg-moss-100 text-moss-700",
            title: t("reports.partners_title", "Clients & Fournisseurs"),
            desc: t(
              "reports.partners_desc",
              "Annuaire des partenaires avec rôle, coordonnées et statut de compte."
            ),
            filters: [
              {
                name: "kind",
                type: "select",
                label: t("reports.filter_kind", "Rôle"),
                options: [
                  { value: "customer", label: t("partners.role_customer", "Client") },
                  { value: "supplier", label: t("partners.role_supplier", "Fournisseur") },
                ],
              },
              {
                name: "status",
                type: "select",
                label: t("reports.filter_status", "Statut"),
                options: [
                  { value: "active", label: t("partners.status_active", "Actif") },
                  { value: "inactive", label: t("partners.status_inactive", "Inactif") },
                ],
              },
            ],
          },
        ],
      },
      {
        key: "commerce",
        title: t("reports.cat_commerce", "Ventes & Achats"),
        reports: [
          {
            slug: "sales-orders",
            stem: "commandes-vente",
            icon: ShoppingCart,
            iconClass: "bg-ochre-100 text-ochre-700",
            title: t("reports.sales_title", "Commandes de Vente"),
            desc: t(
              "reports.sales_desc",
              "Synthèse de toutes les commandes clients, leurs montants et statuts de validation."
            ),
            filters: [
              {
                name: "date_from",
                type: "date",
                label: t("reports.date_from", "Date de début"),
              },
              {
                name: "date_to",
                type: "date",
                label: t("reports.date_to", "Date de fin"),
              },
              {
                name: "status",
                type: "select",
                label: t("reports.filter_status", "Statut"),
                options: statusOptions("sales", [
                  "draft",
                  "confirmed",
                  "partially_delivered",
                  "delivered",
                  "cancelled",
                ]),
              },
              {
                name: "customer_id",
                type: "select",
                label: t("reports.filter_customer", "Client"),
                options: customers,
              },
            ],
          },
          {
            slug: "purchase-orders",
            stem: "commandes-achat",
            icon: Truck,
            iconClass: "bg-terracotta-100 text-terracotta-700",
            title: t("reports.purchases_title", "Commandes d'Achat"),
            desc: t(
              "reports.purchases_desc",
              "Historique des commandes fournisseurs avec montants et statuts de réception."
            ),
            filters: [
              {
                name: "date_from",
                type: "date",
                label: t("reports.date_from", "Date de début"),
              },
              {
                name: "date_to",
                type: "date",
                label: t("reports.date_to", "Date de fin"),
              },
              {
                name: "status",
                type: "select",
                label: t("reports.filter_status", "Statut"),
                options: statusOptions("purchases", [
                  "draft",
                  "confirmed",
                  "partially_received",
                  "received",
                  "cancelled",
                ]),
              },
              {
                name: "supplier_id",
                type: "select",
                label: t("reports.filter_supplier", "Fournisseur"),
                options: suppliers,
              },
            ],
          },
          {
            slug: "invoices",
            stem: "factures",
            icon: FileText,
            iconClass: "bg-aubergine-100 text-aubergine-700",
            title: t("reports.invoices_title", "Factures"),
            desc: t(
              "reports.invoices_desc",
              "Factures émises avec montants, paiements et solde restant dû."
            ),
            filters: [
              {
                name: "date_from",
                type: "date",
                label: t("reports.date_from", "Date de début"),
              },
              {
                name: "date_to",
                type: "date",
                label: t("reports.date_to", "Date de fin"),
              },
              {
                name: "status",
                type: "select",
                label: t("reports.filter_status", "Statut"),
                options: statusOptions("invoices", [
                  "draft",
                  "issued",
                  "partially_paid",
                  "paid",
                  "cancelled",
                ]),
              },
              {
                name: "customer_id",
                type: "select",
                label: t("reports.filter_customer", "Client"),
                options: customers,
              },
            ],
          },
        ],
      },
      {
        key: "stock",
        title: t("reports.cat_stock", "Stock"),
        reports: [
          {
            slug: "stock-movements",
            stem: "mouvements-stock",
            icon: ArrowLeftRight,
            iconClass: "bg-sage-100 text-sage-700",
            title: t("reports.stock_title", "Mouvements de Stock"),
            desc: t(
              "reports.stock_desc",
              "Historique détaillé des entrées, sorties et transferts inter-entrepôts."
            ),
            filters: [
              {
                name: "date_from",
                type: "date",
                label: t("reports.date_from", "Date de début"),
              },
              {
                name: "date_to",
                type: "date",
                label: t("reports.date_to", "Date de fin"),
              },
              {
                name: "movement_type",
                type: "select",
                label: t("reports.filter_type", "Type"),
                options: [
                  { value: "in", label: t("inventory.type_in", "Entrée") },
                  { value: "out", label: t("inventory.type_out", "Sortie") },
                  { value: "transfer", label: t("inventory.type_transfer", "Transfert") },
                ],
              },
              {
                name: "warehouse_id",
                type: "select",
                label: t("reports.filter_warehouse", "Entrepôt"),
                options: warehouses,
              },
            ],
          },
          {
            slug: "stock-levels",
            stem: "niveaux-stock",
            icon: Package,
            iconClass: "bg-moss-100 text-moss-700",
            title: t("reports.stock_levels_title", "Niveaux de Stock"),
            desc: t(
              "reports.stock_levels_desc",
              "Quantités disponibles par produit et par entrepôt."
            ),
            filters: [
              {
                name: "warehouse_id",
                type: "select",
                label: t("reports.filter_warehouse", "Entrepôt"),
                options: warehouses,
              },
            ],
          },
        ],
      },
      {
        key: "accounting",
        title: t("reports.cat_accounting", "Comptabilité"),
        reports: [
          {
            slug: "accounting-journal",
            stem: "journal-comptable",
            icon: BookOpenText,
            iconClass: "bg-aubergine-100 text-aubergine-700",
            title: t("reports.journal_title", "Journal Comptable"),
            desc: t(
              "reports.journal_desc",
              "Écritures comptables par période et par journal, avec débit et crédit."
            ),
            filters: [
              {
                name: "period",
                type: "month",
                label: t("reports.filter_period", "Période (mois)"),
              },
              {
                name: "journal_id",
                type: "select",
                label: t("reports.filter_journal", "Journal"),
                options: journals,
              },
            ],
          },
        ],
      },
    ],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [t, customers, suppliers, warehouses, journals]
  );

  const updateFilter = (slug: string, name: keyof ReportFilters, value: string) => {
    setFilters((prev) => ({
      ...prev,
      [slug]: { ...(prev[slug] ?? EMPTY_FILTERS), [name]: value },
    }));
  };

  const toggleFilters = (slug: string) => {
    setFiltersOpen((prev) => ({ ...prev, [slug]: !prev[slug] }));
  };

  const handleDownload = async (slug: string, stem: string, output: ReportOutput) => {
    setDownloading((prev) => ({ ...prev, [slug]: output }));
    try {
      await downloadReport(slug, stem, output, filters[slug] ?? EMPTY_FILTERS);
      pushToast("success", t("reports.success_download", "Rapport téléchargé avec succès."));
    } catch (err) {
      console.error(`Export error for ${slug}:`, err);
      pushToast(
        "error",
        t("reports.error_export_failed", "Échec du téléchargement du rapport. Veuillez réessayer.")
      );
    } finally {
      setDownloading((prev) => ({ ...prev, [slug]: null }));
    }
  };

  const handlePreview = async (slug: string) => {
    if (open[slug]) {
      setOpen((prev) => ({ ...prev, [slug]: false }));
      return;
    }
    setOpen((prev) => ({ ...prev, [slug]: true }));
    setPreviewLoading((prev) => ({ ...prev, [slug]: true }));
    try {
      const result = await fetchReportPreview(slug, filters[slug] ?? EMPTY_FILTERS);
      setPreview((prev) => ({ ...prev, [slug]: result }));
    } catch (err) {
      console.error(`Preview error for ${slug}:`, err);
      setOpen((prev) => ({ ...prev, [slug]: false }));
      setPreview((prev) => ({ ...prev, [slug]: null }));
      pushToast(
        "error",
        t("reports.error_preview_failed", "Échec du chargement de l'aperçu.")
      );
    } finally {
      setPreviewLoading((prev) => ({ ...prev, [slug]: false }));
    }
  };

  const renderFilters = (report: ReportDef) => {
    const defs = report.filters;
    if (defs.length === 0) return null;
    return (
      <div className="mt-5 grid grid-cols-1 gap-3 rounded-md border border-ink-900/10 bg-sand-50/70 p-4 sm:grid-cols-2">
        {defs.map((def) => (
          <div key={def.name} className={defs.length % 2 === 1 && defs.indexOf(def) === defs.length - 1 ? "sm:col-span-2" : ""}>
            <label className="field-label text-xs">{def.label}</label>
            {def.type === "select" ? (
              <select
                value={filters[report.slug]?.[def.name] ?? ""}
                onChange={(e) => updateFilter(report.slug, def.name, e.target.value)}
                className="input text-xs"
              >
                <option value="">{t("reports.status_all", "Tous")}</option>
                {def.options?.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type={def.type}
                value={filters[report.slug]?.[def.name] ?? ""}
                onChange={(e) => updateFilter(report.slug, def.name, e.target.value)}
                className="input text-xs"
              />
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderPreview = (report: ReportDef) => {
    if (!open[report.slug]) return null;
    const data = preview[report.slug];
    const loading = previewLoading[report.slug];
    return (
      <div className="mt-5">
        <div className="overflow-hidden rounded-md border border-ink-900/10">
          {loading ? (
            <div className="flex items-center justify-center gap-2 bg-white px-4 py-8 text-sm text-ink-600">
              <Loader2 className="h-4 w-4 animate-spin" />
              {t("common.loading", "Chargement...")}
            </div>
          ) : data && data.rows.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-start text-xs">
                  <thead className="bg-sand-100 font-mono text-[11px] font-medium uppercase tracking-widest text-ink-600">
                    <tr>
                      {data.columns.map((column) => (
                        <th key={column} className="whitespace-nowrap px-3 py-2.5 text-start">
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-ink-900/5 bg-white">
                    {data.rows.map((row, rowIndex) => (
                      <tr key={rowIndex} className="hover:bg-sand-50">
                        {row.map((cell, cellIndex) => (
                          <td key={cellIndex} className="whitespace-nowrap px-3 py-2 text-ink-700">
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="border-t border-ink-900/10 bg-sand-50/70 px-4 py-2 text-xs text-ink-600">
                {t("reports.preview_count", "{{total}} ligne(s)", { total: data.total })}
                {data.truncated &&
                  t("reports.preview_truncated", " — aperçu limité aux 50 premières lignes.")}
              </p>
            </>
          ) : (
            <p className="bg-white px-4 py-8 text-center text-sm text-ink-600">
              {t("reports.empty_preview", "Aucune donnée pour ces filtres.")}
            </p>
          )}
        </div>
      </div>
    );
  };

  const activeFilterCount = (report: ReportDef) =>
    report.filters.filter((def) => {
      const value = filters[report.slug]?.[def.name];
      return value !== undefined && value !== "";
    }).length;

  const renderReportRow = (report: ReportDef) => {
    const Icon = report.icon;
    const current = downloading[report.slug];
    const count = activeFilterCount(report);
    const filtersShown = filtersOpen[report.slug] ?? false;
    return (
      <article className="card p-4">
        <div className="flex flex-col gap-4 md:flex-row md:items-center">
          <div className={`shrink-0 rounded-lg p-2.5 ${report.iconClass}`}>
            <Icon className="h-5 w-5" />
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="font-display text-sm font-bold text-ink-900">{report.title}</h3>
            <p className="mt-0.5 text-xs leading-relaxed text-ink-600">{report.desc}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="ghost"
              onClick={() => handlePreview(report.slug)}
              className="shrink-0"
            >
              {open[report.slug] ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
              {open[report.slug]
                ? t("reports.preview_hide", "Masquer")
                : t("reports.preview_button", "Aperçu")}
            </Button>
            {report.filters.length > 0 && (
              <Button
                variant="ghost"
                onClick={() => toggleFilters(report.slug)}
                className="shrink-0"
              >
                {filtersShown ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
                {filtersShown
                  ? t("reports.filters_hide", "Masquer les filtres")
                  : t("reports.filters_button", "Filtres")}
                {count > 0 && (
                  <span className="rounded-full bg-moss-700 px-1.5 py-0.5 text-[10px] font-semibold text-white">
                    {count}
                  </span>
                )}
              </Button>
            )}
            <Button
              variant="primary"
              onClick={() => handleDownload(report.slug, report.stem, "xlsx")}
              disabled={current != null}
              className="shrink-0"
            >
              {current === "xlsx" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <FileSpreadsheet className="h-4 w-4" />
              )}
              {t("reports.export_excel", "Excel (.xlsx)")}
            </Button>
            <Button
              variant="accent"
              onClick={() => handleDownload(report.slug, report.stem, "pdf")}
              disabled={current != null}
              className="shrink-0"
            >
              {current === "pdf" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <FileDown className="h-4 w-4" />
              )}
              {t("reports.export_pdf", "PDF")}
            </Button>
          </div>
        </div>

        {filtersShown && renderFilters(report)}

        {renderPreview(report)}
      </article>
    );
  };

  const visibleCategories =
    activeTab === "all" ? categories : categories.filter((category) => category.key === activeTab);

  const tabs = [
    { key: "all", title: t("reports.tab_all", "Tous") },
    ...categories.map((category) => ({ key: category.key, title: category.title })),
  ];

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow={t("reports.eyebrow", "Rapports")}
        title={t("reports.title", "Rapports & Exports")}
        subtitle={t(
          "reports.subtitle",
          "Générez vos exports Excel et PDF, filtrez les données et prévisualisez les résultats à l'écran."
        )}
      />

      <div className="flex gap-1 overflow-x-auto border-b border-ink-900/10 pb-0">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key)}
              className={`-mb-px flex shrink-0 items-center gap-2 whitespace-nowrap border-b-2 px-3.5 py-2.5 text-sm font-medium transition ${
                isActive
                  ? "border-ochre-500 text-moss-800"
                  : "border-transparent text-ink-600 hover:border-ink-900/20 hover:text-ink-900"
              }`}
            >
              {tab.title}
            </button>
          );
        })}
      </div>

      {visibleCategories.map((category) => (
        <section key={category.key}>
          {activeTab === "all" && (
            <h2 className="mb-3 font-mono text-[11px] font-medium uppercase tracking-eyebrow text-ink-600">
              {category.title}
            </h2>
          )}
          <div className="space-y-4">
            {category.reports.map((report) => (
              <div key={report.slug}>{renderReportRow(report)}</div>
            ))}
          </div>
        </section>
      ))}

      <ToastStack
        toasts={toasts}
        onDismiss={(id) => setToasts((prev) => prev.filter((item) => item.id !== id))}
      />
    </div>
  );
}
