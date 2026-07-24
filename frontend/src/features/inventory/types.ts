export type MovementType = "in" | "out" | "transfer";
export type MovementReason =
  | "purchase" | "sale" | "adjustment" | "transfer"
  | "return_customer" | "return_supplier" | "loss" | "initial" | "other";

export interface StockLevel {
  id: string;
  product: string;
  product_sku: string;
  warehouse: string;
  warehouse_code: string;
  quantity: string;
  unit_symbol: string;
  is_below_threshold: boolean;
  updated_at: string;
}

export interface StockLevelListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: StockLevel[];
}

export interface StockMovement {
  id: string;
  movement_type: MovementType;
  reason: MovementReason;
  product: string;
  product_sku: string;
  warehouse: string;
  warehouse_code: string;
  destination_warehouse: string | null;
  destination_warehouse_code: string | null;
  quantity: string;
  reference: string;
  notes: string;
  created_by_name: string;
  created_at: string;
}

export interface StockMovementListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: StockMovement[];
}

export interface StockInOutFormValues {
  product_id: string;
  warehouse_id: string;
  quantity: string;
  reason: MovementReason;
  reference: string;
  notes: string;
}

export const EMPTY_IN_OUT_FORM: StockInOutFormValues = {
  product_id: "",
  warehouse_id: "",
  quantity: "",
  reason: "adjustment",
  reference: "",
  notes: "",
};

export interface StockTransferFormValues {
  product_id: string;
  from_warehouse_id: string;
  to_warehouse_id: string;
  quantity: string;
  reference: string;
  notes: string;
}

export const EMPTY_TRANSFER_FORM: StockTransferFormValues = {
  product_id: "",
  from_warehouse_id: "",
  to_warehouse_id: "",
  quantity: "",
  reference: "",
  notes: "",
};
