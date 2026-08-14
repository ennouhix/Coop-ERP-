"""
Configuration du module documents.
"""
from django.contrib import admin

from apps.documents.models import DocumentArchive, DocumentTemplate


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ["cooperative", "template_type", "accent_color", "show_logo", "updated_at"]
    list_filter = ["template_type", "show_logo"]


@admin.register(DocumentArchive)
class DocumentArchiveAdmin(admin.ModelAdmin):
    list_display = ["cooperative", "doc_type", "source_number", "filename", "created_at"]
    list_filter = ["doc_type", "source_type"]
