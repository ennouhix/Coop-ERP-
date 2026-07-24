export interface Warehouse {
  id: string;
  code: string;
  name: string;
  address: string;
  city: string;
  phone_number: string;
  manager: string | null;
  manager_name: string;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
}

export interface WarehouseFormValues {
  name: string;
  address: string;
  city: string;
  phone_number: string;
  manager: string | null;
  is_default: boolean;
}

export const EMPTY_WAREHOUSE_FORM: WarehouseFormValues = {
  name: "",
  address: "",
  city: "",
  phone_number: "",
  manager: null,
  is_default: false,
};

export interface TeamMember {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
}
