import { apiClient } from "../../api/client";
import type { SalesOrder, SalesOrderCreateValues, SalesOrderListResponse, SalesOrderStatus } from "./types";

export interface OrderListParams {
  status?: SalesOrderStatus | "";
  page?: number;
}

export async function listSalesOrders(params: OrderListParams): Promise<SalesOrderListResponse> {
  const { data } = await apiClient.get<SalesOrderListResponse>("/sales/orders/", {
    params: { status: params.status || undefined, page: params.page },
  });
  return data;
}

export async function getSalesOrder(id: string): Promise<SalesOrder> {
  const { data } = await apiClient.get<SalesOrder>(`/sales/orders/${id}/`);
  return data;
}

export async function createSalesOrder(values: SalesOrderCreateValues): Promise<SalesOrder> {
  const payload = {
    ...values,
    expected_delivery_date: values.expected_delivery_date || undefined,
    lines: values.lines.map((line) => ({
      product_id: line.product_id,
      quantity_ordered: line.quantity_ordered,
      unit_price: line.unit_price,
    })),
  };
  const { data } = await apiClient.post<SalesOrder>("/sales/orders/", payload);
  return data;
}

export async function confirmSalesOrder(id: string): Promise<SalesOrder> {
  const { data } = await apiClient.post<SalesOrder>(`/sales/orders/${id}/confirm/`);
  return data;
}

export async function cancelSalesOrder(id: string): Promise<SalesOrder> {
  const { data } = await apiClient.post<SalesOrder>(`/sales/orders/${id}/cancel/`);
  return data;
}

export async function deliverSalesOrder(
  id: string, deliveries: { line_id: string; quantity: string }[]
): Promise<SalesOrder> {
  const { data } = await apiClient.post<SalesOrder>(`/sales/orders/${id}/deliver/`, { deliveries });
  return data;
}
