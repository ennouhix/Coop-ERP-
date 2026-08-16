from __future__ import annotations

from django.contrib import admin

from apps.members.models import Member, ShareTransaction


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = [
        "member_number",
        "full_name",
        "cooperative",
        "status",
        "phone_number",
        "join_date",
    ]
    list_filter = ["status", "member_type", "cooperative"]
    search_fields = ["member_number", "first_name", "last_name", "phone_number", "cin"]
    readonly_fields = ["member_number", "created_at", "updated_at"]


@admin.register(ShareTransaction)
class ShareTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "transaction_type",
        "shares_count",
        "amount_per_share",
        "transaction_date",
        "cooperative",
    ]
    list_filter = ["transaction_type", "cooperative"]
    search_fields = ["member__first_name", "member__last_name"]
    readonly_fields = ["created_at", "updated_at"]
