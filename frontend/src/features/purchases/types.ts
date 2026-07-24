export type PurchaseOrderStatus = "draft" | "confirmed" | "partially_received" | "received" | "cancelled";

export interface PurchaseOrderLine {
  id: string;
  product: string;
  product_sku: string;
  product_name: string;
  quantity_ordered: string;
  quantity_received: string;
  quantity_remaining: string;
  unit_price: string;
  line_total: string;
}

export interface PurchaseOrder {
  id: string;
  order_number: string;
  supplier: string;
  supplier_name: string;
  warehouse: string;
  warehouse_code: string;
  status: PurchaseOrderStatus;
  order_date: string;
  expected_delivery_date: string | null;
  notes: string;
  lines: PurchaseOrderLine[];
  total_amount: string;
  created_at: string;
  updated_at: string;
}

export interface PurchaseOrderListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: PurchaseOrder[];
}

export interface LineInput {
  product_id: string;
  quantity_ordered: string;
  unit_price: string;
}

export const EMPTY_LINE: LineInput = { product_id: "", quantity_ordered: "", unit_price: "" };

export interface PurchaseOrderCreateValues {
  supplier_id: string;
  warehouse_id: string;
  order_date: string;
  expected_delivery_date: string;
  notes: string;
  lines: LineInput[];
}

export const EMPTY_PURCHASE_ORDER_FORM: PurchaseOrderCreateValues = {
  supplier_id: "",
  warehouse_id: "",
  order_date: new Date().toISOString().slice(0, 10),
  expected_delivery_date: "",
  notes: "",
  lines: [{ ...EMPTY_LINE }],
};
