import { apiClient } from "../../api/client";
import type { PurchaseOrder, PurchaseOrderCreateValues, PurchaseOrderListResponse, PurchaseOrderStatus } from "./types";

export interface OrderListParams {
  status?: PurchaseOrderStatus | "";
  page?: number;
}

export async function listPurchaseOrders(params: OrderListParams): Promise<PurchaseOrderListResponse> {
  const { data } = await apiClient.get<PurchaseOrderListResponse>("/purchases/orders/", {
    params: { status: params.status || undefined, page: params.page },
  });
  return data;
}

export async function getPurchaseOrder(id: string): Promise<PurchaseOrder> {
  const { data } = await apiClient.get<PurchaseOrder>(`/purchases/orders/${id}/`);
  return data;
}

export async function createPurchaseOrder(values: PurchaseOrderCreateValues): Promise<PurchaseOrder> {
  const payload = {
    ...values,
    expected_delivery_date: values.expected_delivery_date || undefined,
    lines: values.lines.map((line) => ({
      product_id: line.product_id,
      quantity_ordered: line.quantity_ordered,
      unit_price: line.unit_price,
    })),
  };
  const { data } = await apiClient.post<PurchaseOrder>("/purchases/orders/", payload);
  return data;
}

export async function confirmPurchaseOrder(id: string): Promise<PurchaseOrder> {
  const { data } = await apiClient.post<PurchaseOrder>(`/purchases/orders/${id}/confirm/`);
  return data;
}

export async function cancelPurchaseOrder(id: string): Promise<PurchaseOrder> {
  const { data } = await apiClient.post<PurchaseOrder>(`/purchases/orders/${id}/cancel/`);
  return data;
}

export async function receivePurchaseOrder(
  id: string, receipts: { line_id: string; quantity: string }[]
): Promise<PurchaseOrder> {
  const { data } = await apiClient.post<PurchaseOrder>(`/purchases/orders/${id}/receive/`, { receipts });
  return data;
}
