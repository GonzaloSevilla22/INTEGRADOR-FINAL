from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlmodel import Session, func, select, text

from app.models import DetallePedido, Pedido, Pago
from app.modules.estadisticas.schemas import (
    IngresosResponse,
    PedidosPorEstadoItem,
    PedidosPorEstadoResponse,
    ProductoTopItem,
    ProductosTopResponse,
    ResumenResponse,
    VentaItem,
    VentasResponse,
)


class EstadisticasService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def resumen(self) -> ResumenResponse:
        hoy = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        total_pedidos = self._session.exec(
            select(func.count(Pedido.id)).where(Pedido.deleted_at.is_(None))
        ).one()

        pedidos_hoy = self._session.exec(
            select(func.count(Pedido.id)).where(
                Pedido.deleted_at.is_(None),
                Pedido.created_at >= hoy,
            )
        ).one()

        pagos = self._session.exec(
            select(Pago.monto).where(
                Pago.estado == "aprobado",
            )
        ).all()
        ingresos_totales = Decimal(sum(pagos)) if pagos else Decimal("0")

        pagos_hoy = self._session.exec(
            select(Pago.monto).where(
                Pago.estado == "aprobado",
                Pago.created_at >= hoy,
            )
        ).all()
        ingresos_hoy = Decimal(sum(pagos_hoy)) if pagos_hoy else Decimal("0")

        pedidos_pagados = self._session.exec(
            select(func.count(Pedido.id))
            .select_from(Pedido)
            .join(Pago, Pago.pedido_id == Pedido.id)
            .where(
                Pedido.deleted_at.is_(None),
                Pago.estado == "aprobado",
            )
        ).one()

        ticket_promedio = (ingresos_totales / Decimal(pedidos_pagados)) if pedidos_pagados > 0 else Decimal("0")

        total_cant = self._session.exec(
            select(func.coalesce(func.sum(DetallePedido.cantidad), 0)).select_from(DetallePedido)
            .join(Pedido, DetallePedido.pedido_id == Pedido.id)
            .where(Pedido.deleted_at.is_(None))
        ).one()

        return ResumenResponse(
            total_pedidos=total_pedidos,
            pedidos_hoy=pedidos_hoy,
            ingresos_totales=ingresos_totales,
            ingresos_hoy=ingresos_hoy,
            ticket_promedio=ticket_promedio,
            productos_vendidos=int(total_cant),
        )

    def ventas(self) -> VentasResponse:
        pagos = self._session.exec(
            text("""
                SELECT DATE(p.created_at) as fecha,
                       SUM(p.monto) as total,
                       COUNT(p.id) as pedidos
                FROM pagos p
                WHERE p.estado = 'aprobado'
                GROUP BY DATE(p.created_at)
                ORDER BY fecha DESC
                LIMIT 30
            """),
        ).all()

        items = [
            VentaItem(fecha=row[0], total=Decimal(str(row[1])), pedidos=row[2])
            for row in pagos
        ]
        return VentasResponse(data=items)

    def productos_top(self, limit: int = 10) -> ProductosTopResponse:
        rows = self._session.exec(
            text(f"""
                SELECT d.producto_id,
                       d.nombre_snapshot,
                       SUM(d.cantidad) as total_cant,
                       SUM(d.subtotal_snapshot) as total_gen
                FROM detalles_pedido d
                JOIN pedidos p ON p.id = d.pedido_id
                WHERE p.deleted_at IS NULL
                  AND p.estado_codigo != 'CANCELADO'
                GROUP BY d.producto_id, d.nombre_snapshot
                ORDER BY total_cant DESC
                LIMIT {limit}
            """),
        ).all()

        items = [
            ProductoTopItem(
                producto_id=row[0],
                nombre=row[1],
                cantidad_vendida=int(row[2]),
                total_generado=Decimal(str(row[3])),
            )
            for row in rows
        ]
        return ProductosTopResponse(data=items)

    def pedidos_por_estado(self) -> PedidosPorEstadoResponse:
        total = self._session.exec(
            select(func.count(Pedido.id)).where(Pedido.deleted_at.is_(None))
        ).one()

        rows = self._session.exec(
            text("""
                SELECT estado_codigo, COUNT(*) as cantidad
                FROM pedidos
                WHERE deleted_at IS NULL
                GROUP BY estado_codigo
                ORDER BY cantidad DESC
            """),
        ).all()

        total_f = float(total)
        items = [
            PedidosPorEstadoItem(
                estado=row[0],
                cantidad=row[1],
                porcentaje=round((row[1] / total_f * 100), 2) if total_f > 0 else 0,
            )
            for row in rows
        ]
        return PedidosPorEstadoResponse(data=items)

    def ingresos(self) -> IngresosResponse:
        total_ingresos = Decimal("0")
        row = self._session.exec(
            select(func.coalesce(func.sum(Pago.monto), 0)).where(
                Pago.estado == "aprobado",
            )
        ).one()
        total_ingresos = Decimal(str(row))

        import calendar
        now = datetime.now(timezone.utc)
        inicio_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if inicio_mes.month == 1:
            inicio_mes_anterior = inicio_mes.replace(year=inicio_mes.year - 1, month=12)
        else:
            inicio_mes_anterior = inicio_mes.replace(month=inicio_mes.month - 1)

        ingresos_mes = self._session.exec(
            select(func.coalesce(func.sum(Pago.monto), 0)).where(
                Pago.estado == "aprobado",
                Pago.created_at >= inicio_mes,
            )
        ).one()

        ingresos_anterior = self._session.exec(
            select(func.coalesce(func.sum(Pago.monto), 0)).where(
                Pago.estado == "aprobado",
                Pago.created_at >= inicio_mes_anterior,
                Pago.created_at < inicio_mes,
            )
        ).one()

        ingresos_mes_dec = Decimal(str(ingresos_mes))
        ingresos_anterior_dec = Decimal(str(ingresos_anterior))

        variacion = None
        if ingresos_anterior_dec > 0:
            variacion = round(
                float((ingresos_mes_dec - ingresos_anterior_dec) / ingresos_anterior_dec * 100),
                2,
            )

        return IngresosResponse(
            total_ingresos=total_ingresos,
            ingresos_mes_actual=ingresos_mes_dec,
            ingresos_mes_anterior=ingresos_anterior_dec,
            variacion_porcentual=variacion,
        )
