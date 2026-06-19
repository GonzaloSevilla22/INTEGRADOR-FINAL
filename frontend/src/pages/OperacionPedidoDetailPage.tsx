import { useEffect, useRef, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { getPedidoDetail, getHistorialPedido, cambiarEstadoPedido, listPedidos, verifyPayment } from "../services/api";
import type { PedidoDetail, HistorialEstadoPedidoPublic } from "../services/api";

const nextState: Record<string, string> = {
  PENDIENTE: "PAGADO",
  PAGADO: "EN_PREPARACION",
  EN_PREPARACION: "TERMINADO",
  TERMINADO: "ENTREGADO",
};

const stateLabels: Record<string, string> = {
  PENDIENTE: "Pendiente",
  PAGADO: "Pagado",
  EN_PREPARACION: "Preparando",
  TERMINADO: "Terminado",
  ENTREGADO: "Entregado",
  CANCELADO: "Cancelado",
};

const stateColors: Record<string, string> = {
  PENDIENTE: "bg-yellow-100 text-yellow-800",
  PAGADO: "bg-blue-100 text-blue-800",
  EN_PREPARACION: "bg-purple-100 text-purple-800",
  TERMINADO: "bg-teal-100 text-teal-800",
  ENTREGADO: "bg-green-100 text-green-800",
  CANCELADO: "bg-red-100 text-red-800",
};

const cancellableStates = ["PENDIENTE", "PAGADO", "EN_PREPARACION"];

export function OperacionPedidoDetailPage(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const pedidoId = Number(id);
  const queryClient = useQueryClient();

  const pedidoQuery = useQuery({
    queryKey: ["pedido", pedidoId],
    queryFn: () => getPedidoDetail(pedidoId),
    enabled: !Number.isNaN(pedidoId),
  });

  const historialQuery = useQuery({
    queryKey: ["pedido-historial", pedidoId],
    queryFn: () => getHistorialPedido(pedidoId),
    enabled: !Number.isNaN(pedidoId),
  });

  const cancelarMutation = useMutation({
    mutationFn: () => cambiarEstadoPedido(pedidoId, "CANCELADO", "Cancelado por administrador"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pedido", pedidoId] });
      queryClient.invalidateQueries({ queryKey: ["pedido-historial", pedidoId] });
      queryClient.invalidateQueries({ queryKey: ["pedidos"] });
    },
  });

  const avanzarMutation = useMutation({
    mutationFn: (estadoCodigo: string) =>
      cambiarEstadoPedido(pedidoId, estadoCodigo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pedido", pedidoId] });
      queryClient.invalidateQueries({ queryKey: ["pedido-historial", pedidoId] });
      queryClient.invalidateQueries({ queryKey: ["pedidos"] });
    },
  });

  const [verifying, setVerifying] = useState(false);
  const verifiedRef = useRef(false);

  useEffect(() => {
    const pedido = pedidoQuery.data;
    if (!pedido || verifiedRef.current || verifying) return;
    const isMp = pedido.forma_pago_codigo === "MERCADOPAGO" || pedido.forma_pago_codigo === "mercadopago";
    if (pedido.estado_codigo === "PENDIENTE" && isMp) {
      verifiedRef.current = true;
      setVerifying(true);
      verifyPayment(pedido.id)
        .then((res) => {
          if (res.estado === "aprobado" || res.estado === "rechazado") {
            queryClient.invalidateQueries({ queryKey: ["pedido", pedidoId] });
            queryClient.invalidateQueries({ queryKey: ["pedido-historial", pedidoId] });
          }
        })
        .catch(() => {})
        .finally(() => setVerifying(false));
    }
  }, [pedidoQuery.data, pedidoId, queryClient, verifying]);

  if (Number.isNaN(pedidoId)) {
    return <p className="text-red-600">ID de pedido inválido.</p>;
  }

  if (pedidoQuery.isLoading) return <p className="text-slate-600">Cargando pedido...</p>;
  if (pedidoQuery.isError || !pedidoQuery.data) {
    return <p className="text-red-600">Error al cargar el pedido.</p>;
  }

  if (verifying) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-orange-200 border-t-orange-600" />
          <p className="text-slate-600">Verificando estado del pago con MercadoPago...</p>
        </div>
      </div>
    );
  }

  const pedido = pedidoQuery.data;
  const historial = historialQuery.data?.data ?? [];
  const nextEstado = nextState[pedido.estado_codigo];
  const isTerminal = !nextEstado || pedido.estado_codigo === "ENTREGADO" || pedido.estado_codigo === "CANCELADO";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link to="/operaciones-pedidos" className="text-sm text-orange-600 hover:underline">&larr; Volver a pedidos</Link>
          <h1 className="mt-1 text-3xl font-bold text-orange-900">Pedido #{pedido.id}</h1>
        </div>
        <span className={`rounded-full px-4 py-2 text-sm font-semibold ${stateColors[pedido.estado_codigo] ?? "bg-slate-100 text-slate-800"}`}>
          {stateLabels[pedido.estado_codigo] ?? pedido.estado_codigo}
        </span>
      </div>

      {/* Main info grid */}
      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-xl border border-orange-100 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-orange-900">Información del pedido</h2>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between"><dt className="text-slate-600">Usuario ID</dt><dd className="font-mono text-slate-800">{pedido.usuario_id}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-600">Fecha</dt><dd className="text-slate-800">{new Date(pedido.created_at).toLocaleString("es-AR")}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-600">Forma de pago</dt><dd className="text-slate-800">{pedido.forma_pago_codigo ?? "—"}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-600">Notas</dt><dd className="text-slate-800">{pedido.notas ?? "—"}</dd></div>
          </dl>
        </div>

        <div className="rounded-xl border border-orange-100 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-orange-900">Totales</h2>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between"><dt className="text-slate-600">Subtotal</dt><dd className="font-mono text-slate-800">${Number(pedido.subtotal).toLocaleString("es-AR", { minimumFractionDigits: 2 })}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-600">Descuento</dt><dd className="font-mono text-slate-800">-${Number(pedido.descuento).toLocaleString("es-AR", { minimumFractionDigits: 2 })}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-600">Costo envío</dt><dd className="font-mono text-slate-800">${Number(pedido.costo_envio).toLocaleString("es-AR", { minimumFractionDigits: 2 })}</dd></div>
            <div className="border-t border-orange-100 pt-2 flex justify-between"><dt className="font-semibold text-orange-900">Total</dt><dd className="font-mono font-bold text-orange-900">${Number(pedido.total).toLocaleString("es-AR", { minimumFractionDigits: 2 })}</dd></div>
          </dl>
        </div>
      </div>

      {/* Productos */}
      <div className="rounded-xl border border-orange-100 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-orange-900">Productos</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-orange-100">
              <th className="px-3 py-2 text-left font-semibold text-slate-700">Producto</th>
              <th className="px-3 py-2 text-right font-semibold text-slate-700">Cantidad</th>
              <th className="px-3 py-2 text-right font-semibold text-slate-700">Precio unit.</th>
              <th className="px-3 py-2 text-right font-semibold text-slate-700">Subtotal</th>
            </tr>
          </thead>
          <tbody>
            {pedido.detalles.map((d) => (
              <tr key={d.id} className="border-b border-orange-50 hover:bg-orange-50/50">
                <td className="px-3 py-2 font-medium text-slate-800">{d.nombre_snapshot}</td>
                <td className="px-3 py-2 text-right font-mono text-slate-700">{d.cantidad}</td>
                <td className="px-3 py-2 text-right font-mono text-slate-700">${Number(d.precio_snapshot).toLocaleString("es-AR", { minimumFractionDigits: 2 })}</td>
                <td className="px-3 py-2 text-right font-mono text-slate-700">${Number(d.subtotal_snapshot).toLocaleString("es-AR", { minimumFractionDigits: 2 })}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Actions */}
      {!isTerminal && (
        <div className="rounded-xl border border-orange-100 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-orange-900">Acciones</h2>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => avanzarMutation.mutate(nextEstado)}
              disabled={avanzarMutation.isPending}
              className="rounded bg-orange-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-orange-700 disabled:opacity-50"
            >
              {avanzarMutation.isPending
                ? "Procesando..."
                : `Avanzar a ${stateLabels[nextEstado] ?? nextEstado}`}
            </button>

            {cancellableStates.includes(pedido.estado_codigo) && (
              <button
                type="button"
                onClick={() => {
                  if (window.confirm("¿Cancelar este pedido? Se restaurará el stock si corresponde.")) {
                    cancelarMutation.mutate();
                  }
                }}
                disabled={cancelarMutation.isPending}
                className="rounded bg-red-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-red-700 disabled:opacity-50"
              >
                {cancelarMutation.isPending ? "Cancelando..." : "Cancelar pedido"}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Historial */}
      <div className="rounded-xl border border-orange-100 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-orange-900">Historial de cambios</h2>
        {historial.length === 0 ? (
          <p className="text-sm text-slate-500">Sin cambios registrados.</p>
        ) : (
          <div className="space-y-3">
            {[...historial].reverse().map((h: HistorialEstadoPedidoPublic) => (
              <div key={h.id} className="flex items-start gap-3 rounded-lg border border-orange-50 bg-orange-50/50 p-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-orange-200 text-xs font-bold text-orange-800">
                  {h.id}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 text-sm">
                    <span className={`rounded px-2 py-0.5 text-xs font-medium ${stateColors[h.estado_desde_codigo] ?? "bg-slate-100"}`}>
                      {stateLabels[h.estado_desde_codigo] ?? h.estado_desde_codigo}
                    </span>
                    <span className="text-slate-400">&rarr;</span>
                    <span className={`rounded px-2 py-0.5 text-xs font-medium ${stateColors[h.estado_hacia_codigo] ?? "bg-slate-100"}`}>
                      {stateLabels[h.estado_hacia_codigo] ?? h.estado_hacia_codigo}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    {new Date(h.fecha).toLocaleString("es-AR")}
                    {h.motivo ? ` — ${h.motivo}` : ""}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
