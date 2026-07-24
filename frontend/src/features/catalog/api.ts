import { apiClient } from "../../api/client";
import type {
  Category, CategoryFormValues, Product, ProductFormValues, ProductListResponse, Unit, UnitFormValues,
} from "./types";

// --- Unités ---

export async function listUnits(): Promise<Unit[]> {
  const { data } = await apiClient.get<{ results: Unit[] } | Unit[]>("/catalog/units/");
  return Array.isArray(data) ? data : data.results;
}

export async function createUnit(values: UnitFormValues): Promise<Unit> {
  const { data } = await apiClient.post<Unit>("/catalog/units/", values);
  return data;
}

// --- Catégories ---

export async function listCategories(): Promise<Category[]> {
  const { data } = await apiClient.get<{ results: Category[] } | Category[]>("/catalog/categories/");
  return Array.isArray(data) ? data : data.results;
}

export async function createCategory(values: CategoryFormValues): Promise<Category> {
  const { data } = await apiClient.post<Category>("/catalog/categories/", values);
  return data;
}

// --- Produits ---

export interface ProductListParams {
  search?: string;
  category?: string;
  page?: number;
}

export async function listProducts(params: ProductListParams): Promise<ProductListResponse> {
  const { data } = await apiClient.get<ProductListResponse>("/catalog/products/", {
    params: { search: params.search || undefined, category: params.category || undefined, page: params.page },
  });
  return data;
}

export async function getProduct(id: string): Promise<Product> {
  const { data } = await apiClient.get<Product>(`/catalog/products/${id}/`);
  return data;
}

export async function createProduct(values: ProductFormValues): Promise<Product> {
  const { data } = await apiClient.post<Product>("/catalog/products/", values);
  return data;
}

export async function updateProduct(id: string, values: Partial<ProductFormValues>): Promise<Product> {
  const { data } = await apiClient.patch<Product>(`/catalog/products/${id}/`, values);
  return data;
}

export async function deactivateProduct(id: string): Promise<void> {
  await apiClient.post(`/catalog/products/${id}/deactivate/`);
}

export async function reactivateProduct(id: string): Promise<Product> {
  const { data } = await apiClient.post<Product>(`/catalog/products/${id}/reactivate/`);
  return data;
}
