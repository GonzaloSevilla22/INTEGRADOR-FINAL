from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship

from app.core.base import BaseModel, now_utc

if TYPE_CHECKING:
    from app.models.pedido import Pedido
    from app.models.estado_pedido import EstadoPedido
    from app.models.usuario import Usuario


class HistorialEstadoPedido(BaseModel, table=True):
    """
    Historial de cambios de estado del pedido.
    Registra transiciones de estado y quién las realizó.
    Relaciones:
    - N:1 Pedido
    - N:1 EstadoPedido (estado_desde)
    - N:1 EstadoPedido (estado_hacia)
    - N:1 Usuario (quién realizó el cambio)
    """

    __tablename__ = "historiales_estado_pedido"

    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedidos.id", nullable=False, index=True)
    estado_desde_codigo: str = Field(foreign_key="estados_pedido.codigo", max_length=50, nullable=False)
    estado_hacia_codigo: str = Field(foreign_key="estados_pedido.codigo", max_length=50, nullable=False)
    usuario_id: Optional[int] = Field(foreign_key="usuarios.id", nullable=True)
    motivo: Optional[str] = Field(default=None, nullable=True)
    fecha: datetime = Field(default_factory=now_utc, nullable=False, index=True)

    # Relaciones
    pedido: "Pedido" = Relationship(back_populates="historiales")
    estado_desde: Optional["EstadoPedido"] = Relationship(
        back_populates="historiales",
        sa_relationship_kwargs={"foreign_keys": "HistorialEstadoPedido.estado_desde_codigo"}
    )
    estado_hacia: Optional["EstadoPedido"] = Relationship(
        back_populates="historiales_hacia",
        sa_relationship_kwargs={"foreign_keys": "HistorialEstadoPedido.estado_hacia_codigo"}
    )
    usuario: Optional["Usuario"] = Relationship(back_populates="historiales")

    def __repr__(self) -> str:
        return f"HistorialEstadoPedido(pedido_id={self.pedido_id}, {self.estado_desde_codigo} → {self.estado_hacia_codigo})"
