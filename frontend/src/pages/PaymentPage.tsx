import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api, listDireccionesUsuario, updatePedidoDireccion, type DireccionEntregaPublic } from '../services/api'
import { PaymentButton } from '../components/PaymentButton'

interface OrderData {
  id: number
  total: number
  estado_codigo: string
  direccion_entrega_id: number
}

export default function PaymentPage() {
  const { orderId } = useParams<{ orderId: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [order, setOrder] = useState<OrderData | null>(null)
  const [direcciones, setDirecciones] = useState<DireccionEntregaPublic[]>([])
  const [selectedDirId, setSelectedDirId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [cashLoading, setCashLoading] = useState(false)
  const [updatingDir, setUpdatingDir] = useState(false)
  const [paymentInitiated, setPaymentInitiated] = useState(false)

  useEffect(() => {
    if (!user || !orderId) return
    Promise.all([
      api.get(`/pedidos/${orderId}`),
      listDireccionesUsuario(user.id, 0, 100),
    ])
      .then(([pedidoRes, direccionesRes]) => {
        const pedido = pedidoRes.data as OrderData
        setOrder(pedido)
        const dirs = (direccionesRes.data ?? [])
          .filter((d) => d.activo)
          .sort((a, b) => Number(b.es_principal) - Number(a.es_principal))
        setDirecciones(dirs)
        setSelectedDirId(pedido.direccion_entrega_id)
      })
      .catch(() => setError('No se pudo cargar la información'))
      .finally(() => setLoading(false))
  }, [orderId, user])

  const handleCambiarDireccion = async (dirId: number) => {
    if (!order || dirId === order.direccion_entrega_id) return
    setUpdatingDir(true)
    try {
      const updated = await updatePedidoDireccion(order.id, dirId)
      setOrder(prev => prev ? { ...prev, direccion_entrega_id: updated.direccion_entrega_id } : prev)
      setSelectedDirId(updated.direccion_entrega_id)
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Error al actualizar dirección'
      setError(msg)
    } finally {
      setUpdatingDir(false)
    }
  }

  const pagarEnEfectivo = async () => {
    setCashLoading(true)
    try {
      await api.patch(`/pedidos/${orderId}/confirmar`, { forma_pago_codigo: "EFECTIVO" })
      navigate(`/mis-pedidos`)
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || "Error al confirmar pedido"
      setError(msg)
    } finally {
      setCashLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-500">Cargando pedido...</p>
      </div>
    )
  }

  if (error || !order) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center text-center px-4">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Pedido no encontrado</h1>
        <p className="text-gray-500 mb-6">{error}</p>
        <Link to="/" className="bg-blue-500 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-blue-600">
          Volver al Catálogo
        </Link>
      </div>
    )
  }

  const selectedDir = direcciones.find(d => d.id === selectedDirId)

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/carrito" className="text-sm text-blue-600 hover:text-blue-800">&larr; Volver al carrito</Link>
          <h1 className="text-xl font-bold text-gray-900">Finalizar Pedido</h1>
          <div className="w-20" />
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8 space-y-4">
        {/* Resumen del pedido */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Resumen del Pedido #{order.id}
            </h2>
            <Link
              to="/productos"
              className="text-sm text-blue-600 hover:text-blue-800 underline"
            >
              Volver al catálogo
            </Link>
          </div>

          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Estado</span>
              <span className="font-medium text-yellow-600">Pendiente de pago</span>
            </div>
            <hr />
            <div className="flex justify-between text-lg">
              <span className="font-bold text-gray-900">Total a pagar</span>
              <span className="font-bold text-blue-600">
                ${Number(order.total).toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Dirección de entrega */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Dirección de entrega</h2>

          {direcciones.length === 0 ? (
            <p className="text-sm text-gray-500">
              No tenés direcciones cargadas.{' '}
              <Link to="/perfil" className="text-blue-600 underline">Agregá una desde Mi Perfil</Link>
            </p>
          ) : (
            <div className="space-y-2">
              {direcciones.map((dir) => (
                <label
                  key={dir.id}
                  className={`block rounded-lg border p-3 cursor-pointer transition-colors ${
                    selectedDirId === dir.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-blue-300'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <input
                      type="radio"
                      name="direccion"
                      checked={selectedDirId === dir.id}
                      onChange={() => handleCambiarDireccion(dir.id)}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">{dir.alias}</span>
                        {dir.es_principal && (
                          <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                            Principal
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600">{dir.linea1}{dir.linea2 ? `, ${dir.linea2}` : ''}</p>
                      <p className="text-sm text-gray-600">{dir.ciudad}, {dir.provincia} ({dir.codigo_postal})</p>
                    </div>
                  </div>
                </label>
              ))}
              {updatingDir && (
                <p className="text-xs text-blue-600">Actualizando dirección...</p>
              )}
            </div>
          )}
        </div>

        {/* Opciones de pago */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div className="space-y-3">
            {paymentInitiated ? (
              <div className="space-y-3">
                <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-center text-sm text-green-700">
                  Pago iniciado. Completalo en la ventana de MercadoPago y volvé para ver el resultado.
                </div>
                <button
                  onClick={() => navigate(`/pedido/${order.id}`)}
                  className="w-full rounded-lg bg-blue-600 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-blue-700"
                >
                  Ya pagué, ver mi pedido
                </button>
              </div>
            ) : (
              <>
                <PaymentButton pedidoId={order.id} monto={Number(order.total)} onPaymentInitiated={() => setPaymentInitiated(true)} />

                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-200" />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-white px-2 text-gray-400">O</span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={pagarEnEfectivo}
                  disabled={cashLoading}
                  className="w-full rounded-lg border-2 border-green-500 bg-green-50 px-4 py-3 text-sm font-medium text-green-700 transition-colors hover:bg-green-100 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {cashLoading ? "Confirmando..." : "Pagar en efectivo"}
                </button>
                <p className="text-center text-xs text-gray-400">El pedido quedará confirmado y lo abonás al retirar.</p>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
