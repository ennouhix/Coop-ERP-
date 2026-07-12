from __future__ import annotations

from django.contrib import admin

from apps.billing.models import Invoice, InvoiceLine, Payment


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = [f.name for f in Payment._meta.fields]  # ledger immuable

    def has_add_permission(self, request, obj=None) -> bool:  # noqa: ANN001
        return False

    def has_delete_permission(self, request, obj=None) -> bool:  # noqa: ANN001
        return False


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "customer", "status", "issue_date", "due_date", "cooperative"]
    list_filter = ["status", "cooperative"]
    search_fields = ["invoice_number"]
    readonly_fields = ["invoice_number", "created_at", "updated_at"]
    inlines = [InvoiceLineInline, PaymentInline]
