export type DocumentTemplateTypeValue = "delivery_note" | "purchase_order" | "receipt";

export interface DocumentTemplate {
  template_type: DocumentTemplateTypeValue;
  template_type_label: string;
  header_text: string;
  footer_text: string;
  terms_text: string;
  accent_color: string;
  show_logo: boolean;
}

export type DocumentTemplateFormValues = Omit<DocumentTemplate, "template_type" | "template_type_label">;
