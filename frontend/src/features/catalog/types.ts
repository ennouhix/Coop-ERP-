export interface TranslatedText {
  fr: string;
  ar?: string;
}

export type UnitType = "weight" | "volume" | "count" | "length";

export interface Unit {
  id: string;
  name: string;
  symbol: string;
  unit_type: UnitType;
  created_at: string;
}

export interface UnitFormValues {
  name: string;
  symbol: string;
  unit_type: UnitType;
}

export interface Category {
  id: string;
  name: TranslatedText;
  name_display: string;
  parent: string | null;
  created_at: string;
}

export interface CategoryFormValues {
  name: TranslatedText;
  parent: string | null;
}

export interface Product {
  id: string;
  sku: string;
  barcode: string;
  name: TranslatedText;
  name_display: string;
  category: string | null;
  category_name_display: string;
  unit: string;
  unit_symbol: string;
  reference_purchase_price: string;
  reference_sale_price: string;
  minimum_stock_threshold: string;
  description: TranslatedText;
  is_sellable: boolean;
  is_purchasable: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Product[];
}

export interface ProductFormValues {
  barcode: string;
  name: TranslatedText;
  category: string | null;
  unit: string;
  reference_purchase_price: string;
  reference_sale_price: string;
  minimum_stock_threshold: string;
  description: TranslatedText;
  is_sellable: boolean;
  is_purchasable: boolean;
}

export const EMPTY_PRODUCT_FORM: ProductFormValues = {
  barcode: "",
  name: { fr: "", ar: "" },
  category: null,
  unit: "",
  reference_purchase_price: "0",
  reference_sale_price: "0",
  minimum_stock_threshold: "0",
  description: { fr: "", ar: "" },
  is_sellable: true,
  is_purchasable: true,
};
