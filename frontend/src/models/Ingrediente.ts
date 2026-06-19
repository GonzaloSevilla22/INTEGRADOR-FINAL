export interface Ingrediente {
  id: number;
  nombre: string;
  descripcion: string | null;
  es_alergeno: boolean;
  stock_actual: number;
  stock_minimo: number;
  costo_unitario: number;
  unidad_medida: "gramos" | "litros";
  activo: boolean;
  deleted_at: string | null;
}

export interface IngredienteCreate {
  nombre: string;
  descripcion: string | null;
  es_alergeno: boolean;
  stock_actual: number;
  stock_minimo: number;
  costo_unitario: number;
  unidad_medida: "gramos" | "litros";
}

export interface IngredienteUpdate {
  nombre?: string;
  descripcion?: string | null;
  es_alergeno?: boolean;
  stock_actual?: number;
  stock_minimo?: number;
  costo_unitario?: number;
  unidad_medida?: "gramos" | "litros";
}

export interface IngredienteProductoUso {
  producto_id: number;
  producto_nombre: string;
  cantidad: number;
  unidad: "gramos" | "litros";
}

export interface IngredienteDetail extends Ingrediente {
  productos_relacionados: IngredienteProductoUso[];
}
