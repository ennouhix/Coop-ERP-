"""Serializers du module documents (M16)."""

from __future__ import annotations

from rest_framework import serializers

from apps.documents.models import DocumentTemplate, DocumentTemplateType, accent_color_validator


class DocumentTemplateSerializer(serializers.ModelSerializer):
    template_type_label = serializers.SerializerMethodField()

    class Meta:
        model = DocumentTemplate
        fields = [
            "template_type",
            "template_type_label",
            "header_text",
            "footer_text",
            "terms_text",
            "accent_color",
            "show_logo",
        ]
        read_only_fields = ["template_type"]

    def get_template_type_label(self, obj: DocumentTemplate) -> str:
        return obj.get_template_type_display()

    def validate_accent_color(self, value: str) -> str:
        if value:
            accent_color_validator(value)
        return value


class DocumentTemplateTypeSerializer(serializers.Serializer):
    """Un type de document personnalisable, avec sa personnalisation ou les valeurs par défaut."""

    template_type = serializers.ChoiceField(choices=DocumentTemplateType.choices)
    template_type_label = serializers.CharField()
    header_text = serializers.CharField(allow_blank=True, default="")
    footer_text = serializers.CharField(allow_blank=True, default="")
    terms_text = serializers.CharField(allow_blank=True, default="")
    accent_color = serializers.CharField(allow_blank=True, default="")
    show_logo = serializers.BooleanField(default=True)
