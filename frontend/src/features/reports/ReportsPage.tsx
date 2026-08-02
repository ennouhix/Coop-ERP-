import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Users, ArrowLeftRight, TrendingUp, Download, FileSpreadsheet, AlertCircle } from "lucide-react";
import { downloadMembersExcel, downloadStockMovementsExcel, downloadSalesOrdersExcel } from "./api";

export function ReportsPage() {
  const { t } = useTranslation();

  // Stock Movements Date Filters
  const [stockDateFrom, setStockDateFrom] = useState("");
  const [stockDateTo, setStockDateTo] = useState("");

  // Sales Orders Date Filters
  const [salesDateFrom, setSalesDateFrom] = useState("");
  const [salesDateTo, setSalesDateTo] = useState("");

  // Loading & Error States
  const [loadingMap, setLoadingMap] = useState<Record<string, boolean>>({});
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleDownload = async (key: string, downloadFn: () => Promise<void>) => {
    setLoadingMap((prev) => ({ ...prev, [key]: true }));
    setErrorMessage(null);
    try {
      await downloadFn();
    } catch (err) {
      console.error(`Export error for ${key}:`, err);
      setErrorMessage(t("reports.error_export_failed", "Échec du téléchargement du rapport. Veuillez réessayer."));
    } finally {
      setLoadingMap((prev) => ({ ...prev, [key]: false }));
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 text-start">
          {t("reports.title", "Rapports & Exports")}
        </h1>
        <p className="mt-1 text-sm text-gray-500 text-start">
          {t("reports.subtitle", "Exportez les données de votre coopérative au format Excel (.xlsx).")}
        </p>
      </div>

      {/* Error Alert */}
      {errorMessage && (
        <div className="p-4 rounded-md bg-red-50 text-red-700 border border-red-200 flex items-center space-s-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span className="text-sm font-medium">{errorMessage}</span>
        </div>
      )}

      {/* Grid of Report Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* 1. Export Membres */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 flex flex-col justify-between hover:border-emerald-500 transition-colors">
          <div>
            <div className="flex items-center space-s-3 mb-4">
              <div className="p-3 bg-emerald-100 text-emerald-600 rounded-lg">
                <Users className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 text-start">
                  {t("reports.members_title", "Adhérents & Membres")}
                </h3>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700">
                  <FileSpreadsheet className="w-3 h-3 me-1" />
                  Excel (.xlsx)
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-600 text-start mb-6">
              {t("reports.members_desc", "Liste exhaustive de tous les adhérents avec coordonnées, CIN, statut et parts sociales.")}
            </p>
          </div>

          <button
            type="button"
            onClick={() => handleDownload("members", downloadMembersExcel)}
            disabled={loadingMap["members"]}
            className="w-full flex items-center justify-center space-s-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-md text-sm font-medium transition-colors"
          >
            <Download className="w-4 h-4 me-1.5" />
            {loadingMap["members"]
              ? t("common.loading", "Chargement...")
              : t("reports.download_button", "Télécharger")}
          </button>
        </div>

        {/* 2. Export Mouvements de Stock */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 flex flex-col justify-between hover:border-blue-500 transition-colors">
          <div>
            <div className="flex items-center space-s-3 mb-4">
              <div className="p-3 bg-blue-100 text-blue-600 rounded-lg">
                <ArrowLeftRight className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 text-start">
                  {t("reports.stock_title", "Mouvements de Stock")}
                </h3>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700">
                  <FileSpreadsheet className="w-3 h-3 me-1" />
                  Excel (.xlsx)
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-600 text-start mb-4">
              {t("reports.stock_desc", "Historique détaillé des entrées, sorties et transferts inter-entrepôts.")}
            </p>

            {/* Date Filters */}
            <div className="space-y-3 mb-6 bg-gray-50 p-3 rounded-md border border-gray-100">
              <div>
                <label className="block text-xs font-medium text-gray-700 text-start mb-1">
                  {t("reports.date_from", "Date de début")}
                </label>
                <input
                  type="date"
                  value={stockDateFrom}
                  onChange={(e) => setStockDateFrom(e.target.value)}
                  className="w-full text-xs rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 text-start mb-1">
                  {t("reports.date_to", "Date de fin")}
                </label>
                <input
                  type="date"
                  value={stockDateTo}
                  onChange={(e) => setStockDateTo(e.target.value)}
                  className="w-full text-xs rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={() =>
              handleDownload("stock", () =>
                downloadStockMovementsExcel(stockDateFrom, stockDateTo)
              )
            }
            disabled={loadingMap["stock"]}
            className="w-full flex items-center justify-center space-s-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-md text-sm font-medium transition-colors"
          >
            <Download className="w-4 h-4 me-1.5" />
            {loadingMap["stock"]
              ? t("common.loading", "Chargement...")
              : t("reports.download_button", "Télécharger")}
          </button>
        </div>

        {/* 3. Export Commandes de Vente */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 flex flex-col justify-between hover:border-purple-500 transition-colors">
          <div>
            <div className="flex items-center space-s-3 mb-4">
              <div className="p-3 bg-purple-100 text-purple-600 rounded-lg">
                <TrendingUp className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 text-start">
                  {t("reports.sales_title", "Commandes de Vente")}
                </h3>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-50 text-purple-700">
                  <FileSpreadsheet className="w-3 h-3 me-1" />
                  Excel (.xlsx)
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-600 text-start mb-4">
              {t("reports.sales_desc", "Synthèse de toutes les commandes clients, leurs montants et statuts de validation.")}
            </p>

            {/* Date Filters */}
            <div className="space-y-3 mb-6 bg-gray-50 p-3 rounded-md border border-gray-100">
              <div>
                <label className="block text-xs font-medium text-gray-700 text-start mb-1">
                  {t("reports.date_from", "Date de début")}
                </label>
                <input
                  type="date"
                  value={salesDateFrom}
                  onChange={(e) => setSalesDateFrom(e.target.value)}
                  className="w-full text-xs rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 text-start mb-1">
                  {t("reports.date_to", "Date de fin")}
                </label>
                <input
                  type="date"
                  value={salesDateTo}
                  onChange={(e) => setSalesDateTo(e.target.value)}
                  className="w-full text-xs rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
                />
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={() =>
              handleDownload("sales", () =>
                downloadSalesOrdersExcel(salesDateFrom, salesDateTo)
              )
            }
            disabled={loadingMap["sales"]}
            className="w-full flex items-center justify-center space-s-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-md text-sm font-medium transition-colors"
          >
            <Download className="w-4 h-4 me-1.5" />
            {loadingMap["sales"]
              ? t("common.loading", "Chargement...")
              : t("reports.download_button", "Télécharger")}
          </button>
        </div>
      </div>
    </div>
  );
}
