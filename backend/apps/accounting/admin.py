from __future__ import annotations

from django.contrib import admin

from apps.accounting.models import Account, AccountingEntry, AccountingEntryLine, Journal


class AccountingEntryLineInline(admin.TabularInline):
    model = AccountingEntryLine
    extra = 0
    fields = ["account", "label", "debit", "credit"]
    readonly_fields = []


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "account_type", "parent", "is_system", "cooperative"]
    list_filter = ["account_type", "is_system", "cooperative"]
    search_fields = ["code", "name"]
    ordering = ["code"]


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "journal_type", "cooperative"]
    list_filter = ["journal_type", "cooperative"]
    search_fields = ["code"]


@admin.register(AccountingEntry)
class AccountingEntryAdmin(admin.ModelAdmin):
    list_display = [
        "entry_number",
        "journal",
        "entry_date",
        "period",
        "is_posted",
        "cooperative",
    ]
    list_filter = ["is_posted", "journal", "cooperative"]
    search_fields = ["entry_number", "description"]
    readonly_fields = ["entry_number", "period", "created_at", "updated_at"]
    inlines = [AccountingEntryLineInline]


@admin.register(AccountingEntryLine)
class AccountingEntryLineAdmin(admin.ModelAdmin):
    list_display = ["entry", "account", "label", "debit", "credit"]
    list_filter = ["account__account_type"]
    search_fields = ["account__code", "label"]
