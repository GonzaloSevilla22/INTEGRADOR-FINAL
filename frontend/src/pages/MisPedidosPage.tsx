import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getPedidosWebSocketUrl, listPedidos, cancelarPedido, type PedidoPublic } from "../services/api";

const ESTADOS = ["PENDIENTE", "PAGADO", "EN_PREPARACION", "TERMINADO", "ENTREGADO", "CANCELADO"] as const;

const estadoColor: Record<string, string> = {
  PENDIENTE: "bg-yellow-100 text-yellow-800",
  PAGADO: "bg-blue-100 text-blue-800",
  EN_PREPARACION: "bg-purple-100 text-purple-800",
  TERMINADO: "bg-teal-100 text-teal-800",
  ENTREGADO: "bg-green-100 text-green-800",
  CANCELADO: "bg-red-100 text-red-800",
};

export function MisPedidosPage(): JSX.Element {
  const navigate = useNavigate();
  const [pedidos, setPedidos] = useState<PedidoPublic[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchId, setSearchId] = useState("");
  const [filterEstado, setFilterEstado] = useState("");
  const [cancelandoId, setCancelandoId] = useState<number | null>(null);

  const handleCancelar = async (pedido: PedidoPublic) => {
    if (!window.confirm(`¿Cancelar pedido #${pedido.id}?`)) return;
    setCancelandoId(pedido.id);
    try {
      await cancelarPedido(pedido.id, "Cancelado por el cliente");
      navigate("/mis-pedidos");
      setPedidos((prev) => prev.map((p) => p.id === pedido.id ? { ...p, estado_codigo: "CANCELADO" } : p));
    } catch {
      alert("No se pudo cancelar el pedido");
    } finally {
      setCancelandoId(null);
    }
  };

  useEffect(() => {
    const cargarPedidos = async (): Promise<void> => {
      setLoading(true);
      try {
        const data = await listPedidos(0, 50);
        setPedidos(data.data || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error desconocido");
      } finally {
        setLoading(false);
      }
    };

    cargarPedidos();

    const ws = new WebSocket(getPedidosWebSocketUrl());
    ws.onmessage = cargarPedidos;

    return () => { ws.close(); };
  }, []);

  const filtrados = useMemo(() => {
    let items = pedidos;
    if (searchId.trim()) {
      const id = parseInt(searchId, 10);
      if (!Number.isNaN(id)) {
        items = items.filter((p) => p.id === id);
      }
    }
    if (filterEstado) {
      items = items.filter((p) => p.estado_codigo === filterEstado);
    }
    return items;
  }, [pedidos, searchId, filterEstado]);

  if (loading) {
    return (
      <div className="rounded-lg border border-orange-100 bg-white/90 p-8 text-center">
        <p className="text-orange-700">Cargando pedidos...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-100 bg-red-50 p-6">
        <p className="text-red-700">Error: {error}</p>
      </div>
    );
  }

  if (pedidos.length === 0) {
    return (
      <div className="rounded-lg border border-orange-100 bg-white/90 p-8 text-center">
        <p className="text-2xl font-bold text-orange-900">No tienes pedidos aún</p>
        <p className="mt-2 text-orange-700">Comienza a comprar desde nuestro catálogo</p>
        <a
          href="/productos"
          className="mt-4 inline-block rounded bg-orange-500 px-6 py-2 font-medium text-white hover:bg-orange-600"
        >
          Ver Productos
        </a>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold text-orange-900">Mis Pedidos</h1>

      <div className="flex flex-wrap gap-3">
        <input
          type="number"
          placeholder="Buscar por # de pedido"
          value={searchId}
          onChange={(e) => setSearchId(e.target.value)}
          className="min-w-0 flex-1 rounded-lg border border-orange-200 bg-white px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:border-orange-400 focus:outline-none"
        />
        <select
          value={filterEstado}
          onChange={(e) => setFilterEstado(e.target.value)}
          className="rounded-lg border border-orange-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-orange-400 focus:outline-none"
        >
          <option value="">Todos los estados</option>
          {ESTADOS.map((e) => (
            <option key={e} value={e}>{e}</option>
          ))}
        </select>
      </div>

      {filtrados.length === 0 ? (
        <p className="text-sm text-slate-600">No se encontraron pedidos con esos filtros.</p>
      ) : (
        <div className="space-y-3">
          {filtrados.map((pedido) => (
            <Link
              key={pedido.id}
              to={`/cliente/pedido/${pedido.id}`}
              className="block rounded-lg border border-orange-100 bg-white/90 p-4 shadow-sm transition hover:shadow-md hover:border-orange-200"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-orange-900">Pedido #{pedido.id}</h3>
                  <p className="text-sm text-orange-700">
                    {pedido.created_at
                      ? new Date(pedido.created_at).toLocaleDateString("es-AR")
                      : "Sin fecha"}
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  {pedido.estado_codigo === "PENDIENTE" && (
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        handleCancelar(pedido);
                      }}
                      disabled={cancelandoId === pedido.id}
                      className="rounded bg-red-100 px-3 py-1 text-xs font-medium text-red-700 hover:bg-red-200 disabled:opacity-50"
                    >
                      {cancelandoId === pedido.id ? "..." : "Cancelar"}
                    </button>
                  )}
                  <div className="text-right">
                    <span
                      className={`rounded-full px-3 py-1 text-sm font-medium ${estadoColor[pedido.estado_codigo] ?? "bg-gray-100 text-gray-800"}`}
                    >
                      {pedido.estado_codigo}
                    </span>
                    <p className="mt-2 font-bold text-orange-900">${Number(pedido.total).toFixed(2)}</p>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
