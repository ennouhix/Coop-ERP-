export type SalesOrderStatus = "draft" | "confirmed" | "partially_delivered" | "delivered" | "cancelled";

export interface SalesOrderLine {
  id: string;
  product: string;
  product_sku: string;
  product_name: string;
  quantity_ordered: string;
  quantity_delivered: string;
  quantity_remaining: string;
  unit_price: string;
  line_total: string;
}

export interface SalesOrder {
  id: string;
  order_number: string;
  customer: string;
  customer_name: string;
  warehouse: string;
  warehouse_code: string;
  status: SalesOrderStatus;
  order_date: string;
  expected_delivery_date: string | null;
  notes: string;
  lines: SalesOrderLine[];
  total_amount: string;
  created_at: string;
  updated_at: string;
}

export interface SalesOrderListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: SalesOrder[];
}

export interface LineInput {
  product_id: string;
  quantity_ordered: string;
  unit_price: string;
}

export const EMPTY_LINE: LineInput = { product_id: "", quantity_ordered: "", unit_price: "" };

export interface SalesOrderCreateValues {
  customer_id: string;
  warehouse_id: string;
  order_date: string;
  expected_delivery_date: string;
  notes: string;
  lines: LineInput[];
}

export const EMPTY_SALES_ORDER_FORM: SalesOrderCreateValues = {
  customer_id: "",
  warehouse_id: "",
  order_date: new Date().toISOString().slice(0, 10),
  expected_delivery_date: "",
  notes: "",
  lines: [{ ...EMPTY_LINE }],
};
