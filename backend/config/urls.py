"""URLs racine. Chaque app expose ses propres urls.py, inclus ici sous /api/v1/."""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/cooperatives/", include("apps.cooperatives.urls")),
    path("api/v1/users/", include("apps.users.urls")),
    path("api/v1/members/", include("apps.members.urls")),
    path("api/v1/partners/", include("apps.partners.urls")),
    path("api/v1/catalog/", include("apps.catalog.urls")),
    path("api/v1/warehouses/", include("apps.warehouses.urls")),
    path("api/v1/inventory/", include("apps.inventory.urls")),
    path("api/v1/purchases/", include("apps.purchases.urls")),
    path("api/v1/sales/", include("apps.sales.urls")),
    path("api/v1/billing/", include("apps.billing.urls")),
    path("api/v1/dashboard/", include("apps.dashboard.urls")),
    path("api/v1/reporting/", include("apps.reporting.urls")),
    path("api/v1/documents/", include("apps.documents.urls")),
    path("api/v1/audit/", include("apps.audit.urls")),
    path("api/v1/accounting/", include("apps.accounting.urls")),
    path("api/v1/", include("apps.roles_permissions.urls")),
]
