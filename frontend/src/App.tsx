import { useTranslation } from "react-i18next";
import { Navigate, Route, Routes } from "react-router-dom";

import { LoginPage } from "./features/auth/LoginPage";
import { CooperativeSettingsPage } from "./features/cooperative/CooperativeSettingsPage";
import { DashboardPage } from "./features/dashboard/DashboardPage";
import { MemberCreatePage } from "./features/members/MemberCreatePage";
import { MemberDetailPage } from "./features/members/MemberDetailPage";
import { MembersListPage } from "./features/members/MembersListPage";
import { PartnerCreatePage } from "./features/partners/PartnerCreatePage";
import { PartnerDetailPage } from "./features/partners/PartnerDetailPage";
import { PartnersListPage } from "./features/partners/PartnersListPage";
import { ProductCreatePage } from "./features/catalog/ProductCreatePage";
import { ProductDetailPage } from "./features/catalog/ProductDetailPage";
import { ProductsListPage } from "./features/catalog/ProductsListPage";
import { ReferenceDataPage } from "./features/catalog/ReferenceDataPage";
import { WarehouseCreatePage } from "./features/warehouses/WarehouseCreatePage";
import { WarehouseDetailPage } from "./features/warehouses/WarehouseDetailPage";
import { WarehousesListPage } from "./features/warehouses/WarehousesListPage";
import { StockInOutForm } from "./features/inventory/StockInOutForm";
import { StockLevelsPage } from "./features/inventory/StockLevelsPage";
import { StockMovementsPage } from "./features/inventory/StockMovementsPage";
import { StockTransferForm } from "./features/inventory/StockTransferForm";
import { PurchaseOrderCreatePage } from "./features/purchases/PurchaseOrderCreatePage";
import { PurchaseOrderDetailPage } from "./features/purchases/PurchaseOrderDetailPage";
import { PurchaseOrdersListPage } from "./features/purchases/PurchaseOrdersListPage";
import { SalesOrderCreatePage } from "./features/sales/SalesOrderCreatePage";
import { SalesOrderDetailPage } from "./features/sales/SalesOrderDetailPage";
import { SalesOrdersListPage } from "./features/sales/SalesOrdersListPage";
import { AcceptInvitationPage } from "./features/team/AcceptInvitationPage";
import { TeamListPage } from "./features/team/TeamListPage";
import { InvoiceCreatePage } from "./features/billing/InvoiceCreatePage";
import { InvoiceDetailPage } from "./features/billing/InvoiceDetailPage";
import { InvoicesListPage } from "./features/billing/InvoicesListPage";
import { ReportsPage } from "./features/reports/ReportsPage";
import { AppShell } from "./shared/layout/AppShell";
import { NAV_ITEMS } from "./shared/layout/navConfig";
import { ProtectedRoute } from "./shared/routing/ProtectedRoute";
import { ComingSoonPage } from "./shared/ui/ComingSoonPage";
import { LanguageProvider } from "./shared/i18n/LanguageProvider";

export function App() {
  useTranslation(); // force le montage après l'init i18n

  return (
    <LanguageProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/invitations/accept" element={<AcceptInvitationPage />} />

        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <AppShell>
                <Routes>
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/members" element={<MembersListPage />} />
                  <Route path="/members/new" element={<MemberCreatePage />} />
                  <Route path="/members/:id" element={<MemberDetailPage />} />
                  <Route path="/partners" element={<PartnersListPage />} />
                  <Route path="/partners/new" element={<PartnerCreatePage />} />
                  <Route path="/partners/:id" element={<PartnerDetailPage />} />
                  <Route path="/catalog" element={<ProductsListPage />} />
                  <Route path="/catalog/new" element={<ProductCreatePage />} />
                  <Route path="/catalog/reference-data" element={<ReferenceDataPage />} />
                  <Route path="/catalog/:id" element={<ProductDetailPage />} />
                  <Route path="/warehouses" element={<WarehousesListPage />} />
                  <Route path="/warehouses/new" element={<WarehouseCreatePage />} />
                  <Route path="/warehouses/:id" element={<WarehouseDetailPage />} />
                  <Route path="/inventory" element={<StockLevelsPage />} />
                  <Route path="/inventory/movements" element={<StockMovementsPage />} />
                  <Route path="/inventory/movements/in" element={<StockInOutForm direction="in" />} />
                  <Route path="/inventory/movements/out" element={<StockInOutForm direction="out" />} />
                  <Route path="/inventory/movements/transfer" element={<StockTransferForm />} />
                  <Route path="/purchases" element={<PurchaseOrdersListPage />} />
                  <Route path="/purchases/new" element={<PurchaseOrderCreatePage />} />
                  <Route path="/purchases/:id" element={<PurchaseOrderDetailPage />} />
                  <Route path="/sales" element={<SalesOrdersListPage />} />
                  <Route path="/sales/new" element={<SalesOrderCreatePage />} />
                  <Route path="/sales/:id" element={<SalesOrderDetailPage />} />
                  <Route path="/billing" element={<InvoicesListPage />} />
                  <Route path="/billing/new" element={<InvoiceCreatePage />} />
                  <Route path="/billing/:id" element={<InvoiceDetailPage />} />
                  <Route path="/reports" element={<ReportsPage />} />
                  <Route path="/team" element={<TeamListPage />} />
                  <Route path="/settings" element={<CooperativeSettingsPage />} />
                  {NAV_ITEMS.filter((item) => item.comingSoon).map((item) => (
                    <Route
                      key={item.to}
                      path={item.to}
                      element={<ComingSoonPage titleKey={item.labelKey} />}
                    />
                  ))}
                  <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
              </AppShell>
            </ProtectedRoute>
          }
        />
      </Routes>
    </LanguageProvider>
  );
}
