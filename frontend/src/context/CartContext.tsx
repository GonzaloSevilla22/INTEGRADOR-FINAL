import { createContext, useContext, useEffect, useState } from "react";

const CART_STORAGE_KEY = "food_store_cart";

function loadStoredCart(): CartItem[] {
  try {
    const stored = localStorage.getItem(CART_STORAGE_KEY);
    if (!stored) {
      return [];
    }
    const parsed = JSON.parse(stored);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export interface CartItem {
  producto_id: number;
  nombre: string;
  precio: number;
  cantidad: number;
  imagen?: string;
}

interface CartContextValue {
  items: CartItem[];
  total: number;
  agregarProducto: (producto: CartItem) => void;
  removerProducto: (producto_id: number) => void;
  modificarCantidad: (producto_id: number, cantidad: number) => void;
  limpiarCarrito: () => void;
}

const CartContext = createContext<CartContextValue | undefined>(undefined);

export function CartProvider({ children }: { children: React.ReactNode }): JSX.Element {
  const [items, setItems] = useState<CartItem[]>(() => loadStoredCart());

  useEffect(() => {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
  }, [items]);

  const agregarProducto = (producto: CartItem): void => {
    setItems((prev) => {
      const existente = prev.find(item => item.producto_id === producto.producto_id);
      if (existente) {
        return prev.map(item =>
          item.producto_id === producto.producto_id
            ? { ...item, cantidad: item.cantidad + producto.cantidad }
            : item
        );
      }
      return [...prev, producto];
    });
  };

  const removerProducto = (producto_id: number): void => {
    setItems((prev) => prev.filter(item => item.producto_id !== producto_id));
  };

  const modificarCantidad = (producto_id: number, cantidad: number): void => {
    if (cantidad <= 0) {
      removerProducto(producto_id);
      return;
    }
    setItems((prev) =>
      prev.map(item =>
        item.producto_id === producto_id ? { ...item, cantidad } : item
      )
    );
  };

  const limpiarCarrito = (): void => {
    setItems([]);
  };

  const total = items.reduce((sum, item) => sum + item.precio * item.cantidad, 0);

  return (
    <CartContext.Provider value={{ items, total, agregarProducto, removerProducto, modificarCantidad, limpiarCarrito }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart(): CartContextValue {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error("useCart debe usarse dentro de CartProvider");
  }
  return context;
}
