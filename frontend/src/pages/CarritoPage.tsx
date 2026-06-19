import { useCart } from "../context/CartContext";
import { useAuth } from "../context/AuthContext";
import { createPedido, listDireccionesUsuario } from "../services/api";
import { useNavigate } from "react-router-dom";
import { useState } from "react";

export function CarritoPage(): JSX.Element {
  const { items, total, removerProducto, modificarCantidad, limpiarCarrito } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [checkoutLoading, setCheckoutLoading] = useState(false);

    const handleCheckout = async (): Promise<void> => {
    if (!user) {
      navigate("/login?redirect=/carrito");
      return;
    }

    if (items.length === 0) {
      alert("Tu carrito está vacío.");
      return;
    }

    setCheckoutLoading(true);
    try {
      const direcciones = await listDireccionesUsuario(user.id, 0, 50);
      const direccion =
        direcciones.data.find((item) => item.es_principal && item.activo) ??
        direcciones.data.find((item) => item.activo) ??
        null;

      if (!direccion) {
        alert("No tienes dirección de entrega cargada. Carga una dirección para finalizar el checkout.");
        return;
      }

      const pedido = await createPedido({
        direccion_entrega_id: direccion.id,
        detalles: items.map((item) => ({
          producto_id: item.producto_id,
          cantidad: item.cantidad,
        })),
        notas: "Checkout con pago online",
      });

      limpiarCarrito();
      navigate(`/payment/${pedido.id}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "No se pudo realizar el checkout";
      alert(message);
    } finally {
      setCheckoutLoading(false);
    }
  };

  if (items.length === 0) {
    return (
      <div className="rounded-lg border border-orange-100 bg-white/90 p-8 text-center">
        <p className="text-2xl font-bold text-orange-900">Tu carrito está vacío</p>
        <p className="mt-2 text-orange-700">Agrega productos para comenzar</p>
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
      <h1 className="text-3xl font-bold text-orange-900">Mi Carrito</h1>

      <div className="rounded-lg border border-orange-100 bg-white/90 p-6 shadow-sm">
        <div className="space-y-4">
          {items.map((item) => (
            <div
              key={item.producto_id}
              className="flex items-center justify-between border-b border-orange-100 pb-4 last:border-0"
            >
              <div className="flex-1">
                <h3 className="font-semibold text-orange-900">{item.nombre}</h3>
                <p className="text-sm text-orange-700">${item.precio.toFixed(2)}</p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => modificarCantidad(item.producto_id, item.cantidad - 1)}
                  className="rounded border border-orange-200 bg-orange-50 px-2 py-1 text-sm text-orange-900 hover:bg-orange-100"
                >
                  −
                </button>
                <input
                  type="number"
                  min="1"
                  value={item.cantidad}
                  onChange={(e) =>
                    modificarCantidad(item.producto_id, parseInt(e.target.value) || 1)
                  }
                  className="w-12 rounded border border-orange-200 px-2 py-1 text-center text-sm"
                />
                <button
                  type="button"
                  onClick={() => modificarCantidad(item.producto_id, item.cantidad + 1)}
                  className="rounded border border-orange-200 bg-orange-50 px-2 py-1 text-sm text-orange-900 hover:bg-orange-100"
                >
                  +
                </button>
              </div>

              <div className="w-24 text-right">
                <p className="font-semibold text-orange-900">
                  ${(item.precio * item.cantidad).toFixed(2)}
                </p>
              </div>

              <button
                type="button"
                onClick={() => removerProducto(item.producto_id)}
                className="ml-4 rounded bg-red-100 px-3 py-1 text-sm text-red-700 hover:bg-red-200"
              >
                🗑️
              </button>
            </div>
          ))}
        </div>

        <div className="mt-6 space-y-4 border-t border-orange-100 pt-6">
          <div className="flex justify-between text-lg font-bold text-orange-900">
            <span>Total:</span>
            <span>${total.toFixed(2)}</span>
          </div>

          <div className="flex gap-3">
            <a
              href="/productos"
              className="flex-1 rounded border border-orange-200 bg-orange-50 px-4 py-2 text-center font-medium text-orange-900 hover:bg-orange-100"
            >
              Seguir Comprando
            </a>
            <button
              type="button"
              onClick={handleCheckout}
              disabled={checkoutLoading}
              className="flex-1 rounded bg-orange-500 px-4 py-2 font-medium text-white hover:bg-orange-600"
            >
              {checkoutLoading ? "Procesando..." : "Ir a Checkout"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
