from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlmodel import Session

from app.core.rbac import (
    ROLE_ADMIN,
    ROLE_CLIENT,
    ROLE_PEDIDOS,
    STATE_CANCELADO,
    STATE_PAGADO,
    STATE_EN_PREPARACION,
    STATE_TERMINADO,
    STATE_ENTREGADO,
    STATE_PENDIENTE,
    is_terminal,
    normalize_role,
    normalize_state,
)
from app.core.stock_utils import aplicar_stock
from app.core.websocket import manager
from app.models import (
    Pedido,
    DetallePedido,
    HistorialEstadoPedido,
    EstadoPedido,
)
from app.modules.pedidos.pedido_repository import PedidoRepository
from app.modules.pedidos.detalle_pedido_repository import DetallePedidoRepository
from app.modules.pedidos.estado_pedido_repository import EstadoPedidoRepository
from app.modules.pedidos.historial_estado_pedido_repository import HistorialEstadoPedidoRepository
from app.modules.pedidos.unit_of_work import PedidoUnitOfWork
from app.modules.pedidos.schemas import (
    PedidoCreate,
    PedidoPublic,
    PedidoDetail,
    PedidoList,
    DetallePedidoPublic,
    EstadoPedidoPublic,
    HistorialEstadoPedidoPublic,
    HistorialEstadoPedidoList,
    ConfirmarPedidoResponse,
    CambiarEstadoPedidoRequest,
)
from app.modules.payments.repository import PagoRepository


class PedidoService:
    """
    Servicio de negocio para Pedido.
    Usa PedidoUnitOfWork para transacciones atómicas.
    Implementa reglas de negocio, transiciones de estado, y validaciones.
    """

    TRANSICIONES_VALIDAS = {
        STATE_PENDIENTE: [STATE_PAGADO, STATE_CANCELADO],
        STATE_PAGADO: [STATE_EN_PREPARACION, STATE_CANCELADO],
        STATE_EN_PREPARACION: [STATE_TERMINADO, STATE_CANCELADO],
        STATE_TERMINADO: [STATE_ENTREGADO],
        STATE_ENTREGADO: [],
        STATE_CANCELADO: [],
    }

    TRANSICIONES_STOCK = {
        (STATE_PAGADO, STATE_CANCELADO): "restore",
        (STATE_EN_PREPARACION, STATE_CANCELADO): "restore",
    }

    def _aplicar_stock(
        self, uow: PedidoUnitOfWork, producto_id: int, cantidad: int, multiplicador: int = 1
    ) -> None:
        aplicar_stock(uow._session, producto_id, cantidad, multiplicador)

    EVENTOS_WS = {
        STATE_PENDIENTE: "PEDIDO_CREADO",
        STATE_PAGADO: "PEDIDO_PAGADO",
        STATE_EN_PREPARACION: "PEDIDO_EN_PREPARACION",
        STATE_TERMINADO: "PEDIDO_TERMINADO",
        STATE_ENTREGADO: "PEDIDO_ENTREGADO",
        STATE_CANCELADO: "PEDIDO_CANCELADO",
    }

    def __init__(self, session: Session) -> None:
        self._session = session
        self._pedido_repo = PedidoRepository(session)
        self._detalle_repo = DetallePedidoRepository(session)
        self._estado_repo = EstadoPedidoRepository(session)
        self._historial_repo = HistorialEstadoPedidoRepository(session)

    def _can_manage_all(self, roles: list[str]) -> bool:
        normalized = {normalize_role(role) for role in roles}
        return ROLE_ADMIN in normalized or ROLE_PEDIDOS in normalized

    async def _broadcast_event(self, estado_codigo: str, pedido_public: PedidoPublic) -> None:
        event = self.EVENTOS_WS.get(estado_codigo)
        if event is None:
            return
        await manager.broadcast(event, pedido_public.model_dump())

    # ========================================================================
    # CREAR PEDIDO
    # ========================================================================

    def crear_pedido(self, usuario_id: int, data: PedidoCreate) -> ConfirmarPedidoResponse:
        with PedidoUnitOfWork(self._session) as uow:
            usuario = uow.usuarios.get_by_id(usuario_id)
            if not usuario or not usuario.activo or usuario.deleted_at is not None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado",
                )

            direccion = uow.direcciones.get_by_id_and_usuario(data.direccion_entrega_id, usuario_id)
            if not direccion:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dirección de entrega no encontrada",
                )

            detalles_list = []
            subtotal = Decimal("0")

            for detalle_data in data.detalles:
                producto = uow.productos.get_active_by_id(detalle_data.producto_id)
                if not producto:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Producto {detalle_data.producto_id} no encontrado",
                    )

                if not producto.disponible:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Producto {producto.nombre} no disponible",
                    )

                if producto.stock_manual is not None and producto.stock_manual < detalle_data.cantidad:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Stock insuficiente para {producto.nombre}",
                        )

                subtotal_detalle = producto.precio_base * Decimal(detalle_data.cantidad)
                detalles_list.append({
                    "producto_id": producto.id,
                    "cantidad": detalle_data.cantidad,
                    "nombre_snapshot": producto.nombre,
                    "precio_snapshot": producto.precio_base,
                    "subtotal_snapshot": subtotal_detalle,
                })
                subtotal += subtotal_detalle

            costo_envio = Decimal("0")
            total = subtotal - data.descuento + costo_envio

            estado_pendiente = uow.estados.get_by_codigo(STATE_PENDIENTE)
            if not estado_pendiente:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Estado {STATE_PENDIENTE} no configurado",
                )

            pedido = Pedido(
                usuario_id=usuario_id,
                direccion_entrega_id=data.direccion_entrega_id,
                forma_pago_codigo=data.forma_pago_codigo,
                estado_codigo=STATE_PENDIENTE,
                subtotal=subtotal,
                descuento=data.descuento,
                costo_envio=costo_envio,
                total=total,
                notas=data.notas,
            )

            pedido = uow.pedidos.add(pedido)

            for detalle_data in detalles_list:
                detalle = DetallePedido(
                    pedido_id=pedido.id,
                    producto_id=detalle_data["producto_id"],
                    cantidad=detalle_data["cantidad"],
                    nombre_snapshot=detalle_data["nombre_snapshot"],
                    precio_snapshot=detalle_data["precio_snapshot"],
                    subtotal_snapshot=detalle_data["subtotal_snapshot"],
                )
                uow.detalles.add(detalle)

            detalles = uow.detalles.get_by_pedido_id(pedido.id)
            response = ConfirmarPedidoResponse(
                id=pedido.id,
                estado_codigo=pedido.estado_codigo,
                total=pedido.total,
                detalles=[self._detalle_to_public(d) for d in detalles],
                mensaje="Pedido creado. Pendiente de pago.",
            )
        return response

    # ========================================================================
    # CONFIRMAR PEDIDO (PENDIENTE → PAGADO)
    # ========================================================================

    async def confirmar_pedido(self, usuario_id: int, pedido_id: int, forma_pago_codigo: str | None = None) -> ConfirmarPedidoResponse:
        with PedidoUnitOfWork(self._session) as uow:
            pedido = self._get_pedido_seguro(uow, usuario_id, pedido_id)

            if forma_pago_codigo:
                pedido.forma_pago_codigo = forma_pago_codigo

            if pedido.estado_codigo != STATE_PENDIENTE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Pedido en estado {pedido.estado_codigo}, no puede confirmarse",
                )

            if STATE_PAGADO not in self.TRANSICIONES_VALIDAS.get(pedido.estado_codigo, []):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transición de estado no permitida",
                )

            detalles = uow.detalles.get_by_pedido_id(pedido_id)
            for detalle in detalles:
                self._aplicar_stock(uow, detalle.producto_id, detalle.cantidad, multiplicador=1)

            pedido_anterior_codigo = pedido.estado_codigo
            pedido.estado_codigo = STATE_PAGADO
            pedido = uow.pedidos.add(pedido)

            historial = HistorialEstadoPedido(
                pedido_id=pedido_id,
                estado_desde_codigo=pedido_anterior_codigo,
                estado_hacia_codigo=STATE_PAGADO,
                usuario_id=usuario_id,
                motivo="Pedido confirmado",
                fecha=datetime.now(timezone.utc),
            )
            uow.historial.add(historial)

            response = ConfirmarPedidoResponse(
                id=pedido.id,
                estado_codigo=pedido.estado_codigo,
                total=pedido.total,
                detalles=[self._detalle_to_public(d) for d in detalles],
                mensaje="Pedido confirmado exitosamente. Stock descontado.",
            )
            bc_public = self._to_public(pedido)

        await self._broadcast_event(response.estado_codigo, bc_public)
        return response

    # ========================================================================
    # CAMBIAR DIRECCIÓN DE ENTREGA
    # ========================================================================

    def cambiar_direccion(
        self, usuario_id: int, pedido_id: int, nueva_direccion_id: int
    ) -> PedidoDetail:
        with PedidoUnitOfWork(self._session) as uow:
            pedido = uow.pedidos.get_by_id(pedido_id)
            if not pedido or pedido.usuario_id != usuario_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pedido no encontrado",
                )
            if pedido.estado_codigo != STATE_PENDIENTE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se puede cambiar la dirección de un pedido que no está pendiente",
                )

            direccion = uow.direcciones.get_by_id_and_usuario(nueva_direccion_id, usuario_id)
            if not direccion:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dirección de entrega no encontrada",
                )

            pedido.direccion_entrega_id = nueva_direccion_id
            pedido.updated_at = datetime.now(timezone.utc)
            uow.pedidos.add(pedido)

        return self.get_pedido(usuario_id, pedido_id, [ROLE_CLIENT])

    # ========================================================================
    # CANCELAR PEDIDO
    # ========================================================================

    async def cancelar_pedido(
        self,
        usuario_id: int,
        pedido_id: int,
        roles: list[str],
        motivo: Optional[str] = None,
    ) -> PedidoDetail:
        with PedidoUnitOfWork(self._session) as uow:
            pedido = self._get_pedido_seguro(uow, usuario_id, pedido_id, roles)

            is_client = not self._can_manage_all(roles)

            if is_client and pedido.estado_codigo != STATE_PENDIENTE:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo puedes cancelar pedidos en estado PENDIENTE",
                )

            estados_cancelables = [STATE_PENDIENTE, STATE_PAGADO]
            if self._can_manage_all(roles):
                estados_cancelables.append(STATE_EN_PREPARACION)

            if pedido.estado_codigo not in estados_cancelables:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No se puede cancelar pedido en estado {pedido.estado_codigo}",
                )

            if pedido.estado_codigo in [STATE_PAGADO, STATE_EN_PREPARACION]:
                detalles = uow.detalles.get_by_pedido_id(pedido_id)
                for detalle in detalles:
                    self._aplicar_stock(uow, detalle.producto_id, detalle.cantidad, multiplicador=-1)

            pedido_anterior_codigo = pedido.estado_codigo
            pedido.estado_codigo = STATE_CANCELADO
            pedido = uow.pedidos.add(pedido)

            historial = HistorialEstadoPedido(
                pedido_id=pedido_id,
                estado_desde_codigo=pedido_anterior_codigo,
                estado_hacia_codigo=STATE_CANCELADO,
                usuario_id=usuario_id,
                motivo=motivo or "Pedido cancelado",
                fecha=datetime.now(timezone.utc),
            )
            uow.historial.add(historial)

            result = self._to_detail(pedido)
            bc_public = self._to_public(pedido)

        await self._broadcast_event(result.estado_codigo, bc_public)
        return result

    # ========================================================================
    # CAMBIAR ESTADO (ADMIN)
    # ========================================================================

    async def cambiar_estado(
        self,
        usuario_id: int,
        pedido_id: int,
        data: CambiarEstadoPedidoRequest,
    ) -> PedidoDetail:
        with PedidoUnitOfWork(self._session) as uow:
            pedido = uow.pedidos.get_by_id_no_deleted(pedido_id)
            if not pedido:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pedido no encontrado",
                )

            if is_terminal(pedido.estado_codigo):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No se puede modificar un pedido en estado {pedido.estado_codigo}",
                )

            estado_destino_codigo = normalize_state(data.estado_codigo)
            estado_destino = uow.estados.get_by_codigo(estado_destino_codigo)
            if not estado_destino:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Estado {estado_destino_codigo} no existe",
                )

            transiciones_validas = self.TRANSICIONES_VALIDAS.get(pedido.estado_codigo, [])
            if estado_destino_codigo not in transiciones_validas:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Transición de {pedido.estado_codigo} a {estado_destino_codigo} no permitida",
                )

            accion_stock = self.TRANSICIONES_STOCK.get((pedido.estado_codigo, estado_destino_codigo))
            if accion_stock == "restore":
                detalles = uow.detalles.get_by_pedido_id(pedido_id)
                for detalle in detalles:
                    self._aplicar_stock(uow, detalle.producto_id, detalle.cantidad, multiplicador=-1)

            pedido_anterior_codigo = pedido.estado_codigo
            pedido.estado_codigo = estado_destino_codigo
            pedido = uow.pedidos.add(pedido)

            historial = HistorialEstadoPedido(
                pedido_id=pedido_id,
                estado_desde_codigo=pedido_anterior_codigo,
                estado_hacia_codigo=estado_destino_codigo,
                usuario_id=usuario_id,
                motivo=data.motivo or f"Cambio de estado a {estado_destino_codigo}",
                fecha=datetime.now(timezone.utc),
            )
            uow.historial.add(historial)

            result = self._to_detail(pedido)
            bc_public = self._to_public(pedido)

        await self._broadcast_event(result.estado_codigo, bc_public)
        return result

    # ========================================================================
    # OBTENER PEDIDOS
    # ========================================================================

    def get_pedido(self, usuario_id: int, pedido_id: int, roles: list[str]) -> PedidoDetail:
        with PedidoUnitOfWork(self._session) as uow:
            pedido = self._get_pedido_seguro(uow, usuario_id, pedido_id, roles)
            result = self._to_detail(pedido)
        return result

    def list_pedidos(
        self,
        usuario_id: int,
        offset: int = 0,
        limit: int = 20,
        roles: list[str] | None = None,
        estado: str | None = None,
        forma_pago: str | None = None,
        fecha_desde: datetime | None = None,
        fecha_hasta: datetime | None = None,
    ) -> PedidoList:
        roles = roles or []
        with PedidoUnitOfWork(self._session) as uow:
            if self._can_manage_all(roles):
                pedidos = uow.pedidos.get_all_filtered(
                    offset=offset, limit=limit,
                    estado=estado, forma_pago=forma_pago,
                    fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
                )
                total = uow.pedidos.count_all_filtered(
                    estado=estado, forma_pago=forma_pago,
                    fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
                )
            else:
                pedidos = uow.pedidos.get_by_usuario_id(usuario_id, offset=offset, limit=limit)
                total = uow.pedidos.count_by_usuario(usuario_id)
            data = [self._to_public(p) for p in pedidos]
        return PedidoList(data=data, total=total)

    # ========================================================================
    # HISTORIAL
    # ========================================================================

    def get_historial(self, usuario_id: int, pedido_id: int, roles: list[str]) -> HistorialEstadoPedidoList:
        with PedidoUnitOfWork(self._session) as uow:
            self._get_pedido_seguro(uow, usuario_id, pedido_id, roles)
            historiales = uow.historial.get_by_pedido_id(pedido_id)
            data = [self._historial_to_public(h) for h in historiales]
        return HistorialEstadoPedidoList(data=data)

    # ========================================================================
    # HELPERS
    # ========================================================================

    def _get_pedido_seguro(
        self, uow: PedidoUnitOfWork, usuario_id: int, pedido_id: int, roles: list[str] | None = None
    ) -> Pedido:
        roles = roles or []
        if self._can_manage_all(roles):
            pedido = uow.pedidos.get_by_id_no_deleted(pedido_id)
        else:
            pedido = uow.pedidos.get_by_id_no_deleted(pedido_id, usuario_id=usuario_id)

        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pedido no encontrado",
            )

        return pedido

    def _to_public(self, pedido: Pedido) -> PedidoPublic:
        pago = PagoRepository(self._session).get_ultimo_by_pedido(pedido.id)
        return PedidoPublic(
            id=pedido.id,
            usuario_id=pedido.usuario_id,
            direccion_entrega_id=pedido.direccion_entrega_id,
            forma_pago_codigo=pedido.forma_pago_codigo,
            estado_codigo=pedido.estado_codigo,
            subtotal=pedido.subtotal,
            descuento=pedido.descuento,
            costo_envio=pedido.costo_envio,
            total=pedido.total,
            notas=pedido.notas,
            created_at=pedido.created_at,
            pago_estado=pago.estado if pago else None,
            pago_mp_status=pago.mp_status if pago else None,
        )

    def _to_detail(self, pedido: Pedido) -> PedidoDetail:
        estado = self._estado_repo.get_by_codigo(pedido.estado_codigo)
        detalles = self._detalle_repo.get_by_pedido_id(pedido.id)
        pago_repo = PagoRepository(self._session)
        pago = pago_repo.get_ultimo_by_pedido(pedido.id)

        return PedidoDetail(
            id=pedido.id,
            usuario_id=pedido.usuario_id,
            direccion_entrega_id=pedido.direccion_entrega_id,
            forma_pago_codigo=pedido.forma_pago_codigo,
            estado_codigo=pedido.estado_codigo,
            subtotal=pedido.subtotal,
            descuento=pedido.descuento,
            costo_envio=pedido.costo_envio,
            total=pedido.total,
            notas=pedido.notas,
            created_at=pedido.created_at,
            updated_at=pedido.updated_at,
            estado=self._estado_to_public(estado) if estado else EstadoPedidoPublic(
                codigo="UNKNOWN",
                nombre="Desconocido",
            ),
            detalles=[self._detalle_to_public(d) for d in detalles],
            pago_estado=pago.estado if pago else None,
            pago_mp_status=pago.mp_status if pago else None,
            pago_mp_payment_id=pago.mp_payment_id if pago else None,
        )

    def _detalle_to_public(self, detalle: DetallePedido) -> DetallePedidoPublic:
        return DetallePedidoPublic(
            id=detalle.id,
            producto_id=detalle.producto_id,
            cantidad=detalle.cantidad,
            nombre_snapshot=detalle.nombre_snapshot,
            precio_snapshot=detalle.precio_snapshot,
            subtotal_snapshot=detalle.subtotal_snapshot,
            personalizacion=detalle.personalizacion,
        )

    def _estado_to_public(self, estado: EstadoPedido) -> EstadoPedidoPublic:
        return EstadoPedidoPublic(
            codigo=estado.codigo,
            nombre=estado.nombre,
            descripcion=estado.descripcion,
        )

    def _historial_to_public(self, historial: HistorialEstadoPedido) -> HistorialEstadoPedidoPublic:
        return HistorialEstadoPedidoPublic(
            id=historial.id,
            pedido_id=historial.pedido_id,
            estado_desde_codigo=historial.estado_desde_codigo,
            estado_hacia_codigo=historial.estado_hacia_codigo,
            usuario_id=historial.usuario_id,
            motivo=historial.motivo,
            fecha=historial.fecha,
        )
