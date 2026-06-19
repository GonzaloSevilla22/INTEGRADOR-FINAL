from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship

from app.core.base import BaseModel

if TYPE_CHECKING:
    from app.models.usuario import Usuario
    from app.models.direccion_entrega import DireccionEntrega
    from app.models.estado_pedido import EstadoPedido
    from app.models.forma_pago import FormaPago
    from app.models.detalle_pedido import DetallePedido
    from app.models.historial_estado_pedido import HistorialEstadoPedido


class Pedido(BaseModel, table=True):
    """
    Pedido del cliente.
    Relaciones:
    - N:1 Usuario
    - N:1 DireccionEntrega
    - N:1 EstadoPedido
    - 1:N DetallePedido
    - 1:N HistorialEstadoPedido
    Soft delete vía deleted_at
    """

    __tablename__ = "pedidos"

    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuarios.id", nullable=False, index=True)
    direccion_entrega_id: int = Field(foreign_key="direcciones_entrega.id", nullable=False)
    estado_codigo: str = Field(foreign_key="estados_pedido.codigo", max_length=50, nullable=False)
    subtotal: Decimal = Field(default=0, ge=0, max_digits=10, decimal_places=2, nullable=False)
    forma_pago_codigo: Optional[str] = Field(default=None, foreign_key="formas_pago.codigo", max_length=50, nullable=True)
    descuento: Decimal = Field(default=0, ge=0, max_digits=10, decimal_places=2, nullable=False)
    costo_envio: Decimal = Field(default=0, ge=0, max_digits=10, decimal_places=2, nullable=False)
    total: Decimal = Field(default=0, ge=0, max_digits=10, decimal_places=2, nullable=False)
    notas: Optional[str] = Field(default=None, nullable=True)

    # Relaciones
    usuario: "Usuario" = Relationship(back_populates="pedidos")
    direccion_entrega: "DireccionEntrega" = Relationship(back_populates="pedidos")
    estado: "EstadoPedido" = Relationship(back_populates="pedidos")
    forma_pago: Optional["FormaPago"] = Relationship()
    detalles: List["DetallePedido"] = Relationship(back_populates="pedido", cascade_delete=True)
    historiales: List["HistorialEstadoPedido"] = Relationship(back_populates="pedido", cascade_delete=True)

    def __repr__(self) -> str:
        return f"Pedido(id={self.id}, usuario_id={self.usuario_id}, estado={self.estado_codigo}, total={self.total})"
