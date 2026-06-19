import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { useCart } from "../context/CartContext";
import type { Categoria } from "../models/Categoria";
import type { Producto } from "../models/Producto";
import { categoriaService, getProductosPublic, getProductoPublic, getProductosWebSocketUrl } from "../services/api";

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    maximumFractionDigits: 2,
  }).format(value);
}

function getImageUrl(producto: Producto): string {
  if (producto.imagenes_url && producto.imagenes_url.length > 0 && producto.imagenes_url[0]) {
    return producto.imagenes_url[0];
  }

  return "https://images.unsplash.com/photo-1543332164-6e82f355badc?auto=format&fit=crop&w=800&q=80";
}

export function ProductosClientePage(): JSX.Element {
  const { agregarProducto } = useCart();
  const [search, setSearch] = useState("");
  const [categoriaFilter, setCategoriaFilter] = useState("");
  const [soloDisponibles, setSoloDisponibles] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [addingIds, setAddingIds] = useState<Set<number>>(new Set());
  const queryClient = useQueryClient();

  const catIdParam = categoriaFilter ? parseInt(categoriaFilter, 10) : undefined;

  const productosQuery = useQuery({
    queryKey: ["productos", "cliente-catalogo", catIdParam],
    queryFn: () => getProductosPublic(0, 100, catIdParam),
    placeholderData: (prev) => prev,
  });

  const categoriasQuery = useQuery({
    queryKey: ["categorias", "cliente"],
    queryFn: () => categoriaService.getAll(0, 100),
  });

  const productos = productosQuery.data?.data ?? [];
  const categorias = categoriasQuery.data?.data ?? [];

  const filtrados = useMemo(() => {
    let items = productos;
    if (search.trim()) {
      const q = search.toLowerCase();
      items = items.filter((p) => p.nombre.toLowerCase().includes(q));
    }

    if (soloDisponibles) {
      items = items.filter((p) => {
        const stockOk = p.stock_disponible === null || p.stock_disponible > 0;
        return p.disponible && stockOk;
      });
    }
    return items;
  }, [productos, search, categoriaFilter, soloDisponibles]);

  const showToast = useCallback((msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  }, []);

  useEffect(() => {
    const ws = new WebSocket(getProductosWebSocketUrl());
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.event === "PRODUCTO_UPDATED" || payload.event === "INGREDIENTE_UPDATED") {
          queryClient.invalidateQueries({ queryKey: ["productos", "cliente-catalogo"] });
          showToast("Catálogo actualizado");
        }
      } catch {
        // ignore parse errors
      }
    };
    ws.onclose = () => {
      // Reconnect after 5 seconds
      setTimeout(() => {
        // simple reconnect logic will be handled by the effect cleanup/rerun
      }, 5000);
    };
    return () => {
      ws.close();
    };
  }, [queryClient, showToast]);

  if (productosQuery.isLoading) {
    return <p className="text-slate-700">Cargando productos...</p>;
  }

  if (productosQuery.isError) {
    return <p className="text-red-600">No se pudieron cargar los productos.</p>;
  }

  if (productos.length === 0) {
    return (
      <div className="rounded-xl border border-orange-100 bg-white/90 p-8 text-center">
        <h1 className="text-2xl font-bold text-orange-900">Productos</h1>
        <p className="mt-2 text-slate-700">No hay productos disponibles por ahora.</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {toast && (
        <div className="fixed right-4 top-4 z-50 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white shadow-lg">
          {toast}
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-orange-900">Productos</h1>
          <p className="mt-1 text-sm text-slate-700">Explora el catálogo y agrega productos al carrito.</p>
        </div>
        <Link
          to="/carrito"
          className="rounded-lg border border-orange-200 bg-orange-50 px-4 py-2 text-sm font-medium text-orange-900 hover:bg-orange-100"
        >
          Ver carrito
        </Link>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <input
          type="text"
          placeholder="Buscar producto..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="min-w-0 flex-1 rounded-lg border border-orange-200 bg-white px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:border-orange-400 focus:outline-none"
        />
        <select
          value={categoriaFilter}
          onChange={(e) => setCategoriaFilter(e.target.value)}
          className="rounded-lg border border-orange-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-orange-400 focus:outline-none"
        >
          <option value="">Todas las categorías</option>
          {categorias
            .filter((c: Categoria) => c.activo)
            .map((c: Categoria) => (
              <option key={c.id} value={c.id}>{c.nombre}</option>
            ))}
        </select>
        <label className="flex items-center gap-2 rounded-lg border border-orange-200 bg-white px-3 py-2 text-sm text-slate-700 cursor-pointer hover:bg-orange-50">
          <input
            type="checkbox"
            checked={soloDisponibles}
            onChange={(e) => setSoloDisponibles(e.target.checked)}
            className="accent-orange-500"
          />
          Solo disponibles
        </label>
      </div>

      {filtrados.length === 0 ? (
        <p className="text-sm text-slate-600">No se encontraron productos con esos filtros.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtrados.map((producto) => {
            const stockDisponible = producto.stock_disponible;
            const tieneStock = stockDisponible === null || stockDisponible > 0;
            const puedeAgregar = producto.disponible && tieneStock;

            return (
              <article
                key={producto.id}
                className="flex h-full flex-col overflow-hidden rounded-xl border border-orange-100 bg-white shadow-sm"
              >
                <img
                  src={getImageUrl(producto)}
                  alt={producto.nombre}
                  className="h-44 w-full object-cover"
                  loading="lazy"
                />

                <div className="flex flex-1 flex-col gap-3 p-4">
                  <div>
                    <h2 className="text-lg font-semibold text-orange-950">{producto.nombre}</h2>
                    <p className="mt-1 text-sm text-slate-700 line-clamp-2">{producto.descripcion || "Sin descripción"}</p>
                  </div>

                  <div className="space-y-1 text-sm text-slate-700">
                    <p className="font-semibold text-orange-900">{formatCurrency(Number(producto.precio_base))}</p>
                    <p>
                      Disponibilidad:{" "}
                      <span className={producto.disponible ? "font-medium text-green-700" : "font-medium text-red-700"}>
                        {producto.disponible ? "Disponible" : "No disponible"}
                      </span>
                    </p>
                    <p>
                      Stock:{" "}
                      <span className="font-medium text-slate-900">
                        {stockDisponible === null ? "No aplica" : stockDisponible}
                      </span>
                    </p>
                  </div>

                  <button
                    type="button"
                    disabled={!puedeAgregar || addingIds.has(producto.id)}
                    onClick={async () => {
                      setAddingIds((prev) => new Set(prev).add(producto.id));
                      try {
                        const fresh = await getProductoPublic(producto.id);
                        agregarProducto({
                          producto_id: fresh.id,
                          nombre: fresh.nombre,
                          precio: Number(fresh.precio_base),
                          cantidad: 1,
                          imagen: fresh.imagenes_url?.[0] ?? undefined,
                        });
                        window.alert("Producto agregado al carrito");
                      } catch {
                        window.alert("Error al obtener precio actualizado");
                      } finally {
                        setAddingIds((prev) => {
                          const next = new Set(prev);
                          next.delete(producto.id);
                          return next;
                        });
                      }
                    }}
                    className="mt-auto rounded-lg px-4 py-2 text-sm font-medium text-white shadow-sm disabled:cursor-not-allowed disabled:bg-slate-400 bg-orange-500 hover:bg-orange-600"
                  >
                    {addingIds.has(producto.id) ? "Agregando..." : (puedeAgregar ? "Agregar al carrito" : "No disponible")}
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
