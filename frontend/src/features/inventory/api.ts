import { apiClient } from "../../api/client";
import type {
  MovementReason, StockInOutFormValues, StockLevelListResponse, StockMovement,
  StockMovementListResponse, StockTransferFormValues,
} from "./types";

export interface StockLevelParams {
  product?: string;
  warehouse?: string;
  page?: number;
}

export async function listStockLevels(params: StockLevelParams): Promise<StockLevelListResponse> {
  const { data } = await apiClient.get<StockLevelListResponse>("/inventory/stock-levels/", {
    params: { product: params.product || undefined, warehouse: params.warehouse || undefined, page: params.page },
  });
  return data;
}

export async function listLowStock(): Promise<StockLevelListResponse> {
  const { data } = await apiClient.get<StockLevelListResponse>("/inventory/stock-levels/low-stock/");
  return data;
}

export interface MovementListParams {
  product?: string;
  warehouse?: string;
  movement_type?: string;
  reason?: MovementReason | "";
  page?: number;
}

export async function listMovements(params: MovementListParams): Promise<StockMovementListResponse> {
  const { data } = await apiClient.get<StockMovementListResponse>("/inventory/movements/", {
    params: {
      product: params.product || undefined,
      warehouse: params.warehouse || undefined,
      movement_type: params.movement_type || undefined,
      reason: params.reason || undefined,
      page: params.page,
    },
  });
  return data;
}

export async function recordStockIn(values: StockInOutFormValues): Promise<StockMovement> {
  const { data } = await apiClient.post<StockMovement>("/inventory/movements/in/", values);
  return data;
}

export async function recordStockOut(values: StockInOutFormValues): Promise<StockMovement> {
  const { data } = await apiClient.post<StockMovement>("/inventory/movements/out/", values);
  return data;
}

export async function recordStockTransfer(values: StockTransferFormValues): Promise<StockMovement> {
  const { data } = await apiClient.post<StockMovement>("/inventory/movements/transfer/", values);
  return data;
}
