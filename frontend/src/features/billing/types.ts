export type InvoiceStatus = "draft" | "issued" | "partially_paid" | "paid" | "cancelled";
export type PaymentMethod = "cash" | "bank_transfer" | "check" | "mobile_payment" | "other";

export interface InvoiceLine {
  id: string;
  product: string;
  product_sku: string;
  description: string;
  quantity: string;
  unit_price: string;
  line_total: string;
}

export interface Payment {
  id: string;
  amount: string;
  payment_date: string;
  payment_method: PaymentMethod;
  reference: string;
  notes: string;
  created_at: string;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  customer: string;
  customer_name: string;
  sales_order: string | null;
  order_number: string | null;
  status: InvoiceStatus;
  issue_date: string;
  due_date: string;
  notes: string;
  lines: InvoiceLine[];
  payments: Payment[];
  total_amount: string;
  amount_paid: string;
  balance_due: string;
  is_overdue: boolean;
  created_at: string;
  updated_at: string;
}

export interface InvoiceListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Invoice[];
}

export interface ManualLineInput {
  product_id: string;
  description: string;
  quantity: string;
  unit_price: string;
}

export const EMPTY_MANUAL_LINE: ManualLineInput = { product_id: "", description: "", quantity: "", unit_price: "" };

export interface ManualInvoiceCreateValues {
  customer_id: string;
  issue_date: string;
  due_date: string;
  notes: string;
  lines: ManualLineInput[];
}

export const EMPTY_MANUAL_INVOICE_FORM: ManualInvoiceCreateValues = {
  customer_id: "",
  issue_date: new Date().toISOString().slice(0, 10),
  due_date: "",
  notes: "",
  lines: [{ ...EMPTY_MANUAL_LINE }],
};

export interface PaymentFormValues {
  amount: string;
  payment_date: string;
  payment_method: PaymentMethod;
  reference: string;
  notes: string;
}

export const EMPTY_PAYMENT_FORM: PaymentFormValues = {
  amount: "",
  payment_date: new Date().toISOString().slice(0, 10),
  payment_method: "cash",
  reference: "",
  notes: "",
};
