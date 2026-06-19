import { useEffect, useMemo, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  cambiarEstadoPedido,
  getPedidosWebSocketUrl,
  listPedidos,
  type PedidoPublic,
  type PedidosFilter,
} from "../services/api";

function asNumber(value: number | string): number {
  return Number(value ?? 0);
}

const estadoColor: Record<string, string> = {
  PENDIENTE: "text-yellow-600",
  PAGADO: "text-blue-600",
  EN_PREPARACION: "text-purple-600",
  TERMINADO: "text-teal-600",
  ENTREGADO: "text-green-700",
  CANCELADO: "text-red-600",
};

const estadoBadgeBg: Record<string, string> = {
  PENDIENTE: "bg-yellow-500",
  PAGADO: "bg-blue-500",
  EN_PREPARACION: "bg-purple-500",
  TERMINADO: "bg-teal-500",
  ENTREGADO: "bg-green-600",
  CANCELADO: "bg-red-500",
};

const FILTER_ESTADOS = ["", "PENDIENTE", "PAGADO", "EN_PREPARACION", "TERMINADO", "ENTREGADO", "CANCELADO"] as const;
const FORMAS_PAGO = ["", "EFECTIVO", "MERCADOPAGO", "TRANSFERENCIA"] as const;

function puedeCancelar(estado: string): boolean {
  return ["PENDIENTE", "PAGADO", "EN_PREPARACION"].includes(estado);
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "-";
  return new Date(iso).toLocaleDateString("es-AR", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export function OperacionesPedidosPage(): JSX.Element {
  const { hasRole } = useAuth();
  const canOperate = hasRole("ADMIN") || hasRole("PEDIDOS");

  // ---- Stats (all pedidos) ----
  const [allPedidos, setAllPedidos] = useState<PedidoPublic[]>([]);
  const [statsLoading, setStatsLoading] = useState(false);
  const [statsError, setStatsError] = useState<string | null>(null);

  const cargarAllPedidos = useCallback(async (): Promise<void> => {
    setStatsLoading(true);
    try {
      const data = await listPedidos(0, 100);
      setAllPedidos(data.data || []);
    } catch (err) {
      setStatsError(err instanceof Error ? err.message : "Error cargando pedidos");
    } finally {
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => {
    cargarAllPedidos();
    const ws = new WebSocket(getPedidosWebSocketUrl());
    ws.onmessage = () => { cargarAllPedidos(); cargarTabla(); };
    return () => ws.close();
  }, [cargarAllPedidos]);

  const stats = useMemo(() => {
    const pendientes = allPedidos.filter((p) => p.estado_codigo === "PENDIENTE");
    const enPreparacion = allPedidos.filter((p) => p.estado_codigo === "EN_PREPARACION");
    const entregados = allPedidos.filter((p) => p.estado_codigo === "ENTREGADO");
    return {
      total: allPedidos.length,
      pendientes: pendientes.length,
      enPreparacion: enPreparacion.length,
      entregados: entregados.length,
    };
  }, [allPedidos]);

  // ---- Filtered table ----
  const [tablaPedidos, setTablaPedidos] = useState<PedidoPublic[]>([]);
  const [tablaTotal, setTablaTotal] = useState(0);
  const [tablaLoading, setTablaLoading] = useState(false);
  const [tablaError, setTablaError] = useState<string | null>(null);

  const [filtroEstado, setFiltroEstado] = useState("");
  const [filtroFormaPago, setFiltroFormaPago] = useState("");
  const [filtroFechaDesde, setFiltroFechaDesde] = useState("");
  const [filtroFechaHasta, setFiltroFechaHasta] = useState("");
  const [page, setPage] = useState(0);
  const pageSize = 30;

  const cargarTabla = useCallback(async () => {
    setTablaLoading(true);
    setTablaError(null);
    try {
      const filter: PedidosFilter = {};
      if (filtroEstado) filter.estado = filtroEstado;
      if (filtroFormaPago) filter.forma_pago = filtroFormaPago;
      if (filtroFechaDesde) filter.fecha_desde = new Date(filtroFechaDesde).toISOString();
      if (filtroFechaHasta) {
        const end = new Date(filtroFechaHasta);
        end.setHours(23, 59, 59, 999);
        filter.fecha_hasta = end.toISOString();
      }
      const data = await listPedidos(page * pageSize, pageSize, filter);
      setTablaPedidos(data.data);
      setTablaTotal(data.total);
    } catch (err) {
      setTablaError(err instanceof Error ? err.message : "Error al cargar pedidos");
    } finally {
      setTablaLoading(false);
    }
  }, [filtroEstado, filtroFormaPago, filtroFechaDesde, filtroFechaHasta, page]);

  useEffect(() => {
    cargarTabla();
  }, [cargarTabla]);

  const totalPages = Math.ceil(tablaTotal / pageSize);

  // ---- Actions ----
  const [operating, setOperating] = useState<number | null>(null);

  const avanzarEstado = async (pedido: PedidoPublic, nuevoEstado: string): Promise<void> => {
    setOperating(pedido.id);
    try {
      await cambiarEstadoPedido(pedido.id, nuevoEstado);
      await Promise.all([cargarAllPedidos(), cargarTabla()]);
    } catch (err) {
      setStatsError(err instanceof Error ? err.message : "No se pudo cambiar el estado");
    } finally {
      setOperating(null);
    }
  };

  const cancelarPedido = async (pedido: PedidoPublic): Promise<void> => {
    setOperating(pedido.id);
    try {
      await cambiarEstadoPedido(pedido.id, "CANCELADO", "Cancelado por administrador");
      await Promise.all([cargarAllPedidos(), cargarTabla()]);
    } catch (err) {
      setStatsError(err instanceof Error ? err.message : "No se pudo cancelar el pedido");
    } finally {
      setOperating(null);
    }
  };

  const siguienteEstado = (estado: string): string | null => {
    const flujo: Record<string, string | null> = {
      PENDIENTE: "PAGADO",
      PAGADO: "EN_PREPARACION",
      EN_PREPARACION: "TERMINADO",
      TERMINADO: "ENTREGADO",
      ENTREGADO: null,
      CANCELADO: null,
    };
    return flujo[estado] ?? null;
  };

  // ---- Render ----
  if (statsLoading && allPedidos.length === 0) {
    return <p className="text-slate-700">Cargando pedidos...</p>;
  }

  if (statsError && allPedidos.length === 0) {
    return <p className="text-red-600">{statsError}</p>;
  }

  return (
    <section className="rounded-3xl border border-orange-100 bg-white/90 p-5 shadow-sm backdrop-blur">
      <div className="mb-5">
        <h1 className="text-3xl font-semibold text-orange-950">Operaciones de Pedidos</h1>
        <p className="mt-2 text-sm text-slate-600">
          {stats.total} pedidos &middot; {stats.pendientes} pendientes &middot; {stats.enPreparacion} en preparación &middot; {stats.entregados} entregados
        </p>
      </div>

      {/* Filters */}
      <div className="mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Estado</label>
          <select
            value={filtroEstado}
            onChange={(e) => { setFiltroEstado(e.target.value); setPage(0); }}
            className="w-full rounded-lg border border-orange-200 bg-white px-3 py-2 text-sm"
          >
            {FILTER_ESTADOS.map((e) => (
              <option key={e} value={e}>{e || "Todos los estados"}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Forma de pago</label>
          <select
            value={filtroFormaPago}
            onChange={(e) => { setFiltroFormaPago(e.target.value); setPage(0); }}
            className="w-full rounded-lg border border-orange-200 bg-white px-3 py-2 text-sm"
          >
            {FORMAS_PAGO.map((f) => (
              <option key={f} value={f}>{f || "Todas"}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Desde</label>
          <input
            type="date"
            value={filtroFechaDesde}
            onChange={(e) => { setFiltroFechaDesde(e.target.value); setPage(0); }}
            className="w-full rounded-lg border border-orange-200 bg-white px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-slate-600">Hasta</label>
          <input
            type="date"
            value={filtroFechaHasta}
            onChange={(e) => { setFiltroFechaHasta(e.target.value); setPage(0); }}
            className="w-full rounded-lg border border-orange-200 bg-white px-3 py-2 text-sm"
          />
        </div>
      </div>

      {tablaError && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{tablaError}</div>
      )}

      <div className="overflow-x-auto rounded-xl border border-orange-100">
        <table className="w-full min-w-[700px] text-sm">
          <thead className="bg-orange-50 text-left text-xs uppercase text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">#</th>
              <th className="px-4 py-3 font-medium">Cliente</th>
              <th className="px-4 py-3 font-medium">Estado</th>
              <th className="px-4 py-3 font-medium">Pago</th>
              <th className="px-4 py-3 font-medium">Total</th>
              <th className="px-4 py-3 font-medium">Fecha</th>
              <th className="px-4 py-3 font-medium">Detalle</th>
              {canOperate ? <th className="px-4 py-3 font-medium">Operación</th> : null}
            </tr>
          </thead>
          <tbody className="divide-y divide-orange-100">
            {tablaPedidos.length === 0 && !tablaLoading && (
              <tr>
                <td colSpan={canOperate ? 8 : 7} className="px-4 py-8 text-center text-slate-500">
                  No se encontraron pedidos
                </td>
              </tr>
            )}
            {tablaPedidos.map((pedido) => (
              <tr key={pedido.id} className="hover:bg-orange-50/50">
                <td className="px-4 py-3 font-mono text-xs text-slate-500">#{pedido.id}</td>
                <td className="px-4 py-3 text-slate-700">{pedido.usuario_id}</td>
                <td className="px-4 py-3">
                  <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium text-white ${estadoBadgeBg[pedido.estado_codigo] ?? "bg-slate-400"}`}>
                    {pedido.estado_codigo}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-700">{pedido.forma_pago_codigo ?? "—"}</td>
                <td className="px-4 py-3 font-mono text-slate-800 font-medium">${asNumber(pedido.total).toFixed(2)}</td>
                <td className="px-4 py-3 text-xs text-slate-500">{formatDate(pedido.created_at)}</td>
                <td className="px-4 py-3">
                  <Link
                    to={`/operaciones-pedidos/${pedido.id}`}
                    className="rounded bg-blue-100 px-2.5 py-1 text-xs font-medium text-blue-800 hover:bg-blue-200"
                  >
                    Ver
                  </Link>
                </td>
                {canOperate ? (
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      {siguienteEstado(pedido.estado_codigo) ? (
                        <button
                          type="button"
                          onClick={() => avanzarEstado(pedido, siguienteEstado(pedido.estado_codigo) as string)}
                          disabled={operating === pedido.id}
                          className="rounded bg-green-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-green-700 disabled:opacity-50"
                        >
                          {siguienteEstado(pedido.estado_codigo)}
                        </button>
                      ) : null}
                      {puedeCancelar(pedido.estado_codigo) ? (
                        <button
                          type="button"
                          onClick={() => {
                            if (window.confirm("¿Cancelar este pedido?")) {
                              cancelarPedido(pedido);
                            }
                          }}
                          disabled={operating === pedido.id}
                          className="rounded bg-red-500 px-2.5 py-1 text-xs font-semibold text-white hover:bg-red-600 disabled:opacity-50"
                        >
                          Cancelar
                        </button>
                      ) : null}
                      {!siguienteEstado(pedido.estado_codigo) && !puedeCancelar(pedido.estado_codigo) ? (
                        <span className="text-xs text-slate-500">Terminal</span>
                      ) : null}
                    </div>
                  </td>
                ) : null}
              </tr>
            ))}
            {tablaLoading && (
              <tr>
                <td colSpan={canOperate ? 8 : 7} className="px-4 py-8 text-center text-slate-500">Cargando...</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-between text-sm text-slate-600">
          <span>{tablaTotal} pedidos encontrados</span>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="rounded bg-orange-100 px-3 py-1.5 font-medium text-orange-800 hover:bg-orange-200 disabled:opacity-50"
            >
              ← Anterior
            </button>
            <span>Página {page + 1} de {totalPages}</span>
            <button
              onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
              disabled={page >= totalPages - 1}
              className="rounded bg-orange-100 px-3 py-1.5 font-medium text-orange-800 hover:bg-orange-200 disabled:opacity-50"
            >
              Siguiente →
            </button>
          </div>
        </div>
      )}

      {!tablaLoading && totalPages <= 1 && (
        <p className="mt-4 text-sm text-slate-500">{tablaTotal} pedidos encontrados</p>
      )}
    </section>
  );
}
