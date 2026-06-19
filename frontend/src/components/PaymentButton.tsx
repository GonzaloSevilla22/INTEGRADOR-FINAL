import { useState } from 'react'
import { api } from '../services/api'

interface PaymentButtonProps {
  pedidoId: number
  monto: number
  onPaymentInitiated?: () => void
}

export function PaymentButton({ pedidoId, monto, onPaymentInitiated }: PaymentButtonProps) {
  const [loading, setLoading] = useState(false)
  const [opened, setOpened] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handlePagar = async () => {
    setLoading(true)
    setError(null)

    try {
      const res = await api.post('/api/v1/pagos/create-preference', {
        pedido_id: pedidoId,
      })
      const { init_point } = res.data
      if (init_point) {
        window.open(init_point, '_blank')
        setOpened(true)
        onPaymentInitiated?.()
      } else {
        setError('No se pudo obtener el link de pago')
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Error al iniciar el pago'
      setError(detail)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-2">
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {opened ? (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 text-center text-sm text-blue-700">
          Pago iniciado en una nueva ventana. Completá el pago y volvé a esta página.
        </div>
      ) : (
        <button
          onClick={handlePagar}
          disabled={loading}
          className="w-full rounded-lg bg-blue-500 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Iniciando pago...
            </span>
          ) : (
            `Pagar $${monto.toFixed(2)} con MercadoPago`
          )}
        </button>
      )}

      <p className="text-center text-xs text-gray-400">Pago seguro vía MercadoPago</p>
    </div>
  )
}
