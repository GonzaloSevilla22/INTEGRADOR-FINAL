from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship

from app.core.base import BaseModel

if TYPE_CHECKING:
    from app.models.pedido import Pedido
    from app.models.producto import Producto


class DetallePedido(BaseModel, table=True):
    """
    Detalle de un pedido.
    Incluye snapshots del producto en el momento de la compra.
    Relaciones:
    - N:1 Pedido
    - N:1 Producto (referencial)
    Soft delete vía deleted_at
    """

    __tablename__ = "detalles_pedido"

    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: int = Field(foreign_key="pedidos.id", nullable=False, index=True)
    producto_id: int = Field(foreign_key="productos.id", nullable=False)
    cantidad: int = Field(ge=1, nullable=False)
    
    # Snapshots del producto al momento de la compra
    nombre_snapshot: str = Field(max_length=150, nullable=False)
    precio_snapshot: Decimal = Field(ge=0, max_digits=10, decimal_places=2, nullable=False)
    subtotal_snapshot: Decimal = Field(ge=0, max_digits=10, decimal_places=2, nullable=False)
    personalizacion: Optional[str] = Field(default=None, max_length=500)

    # Relaciones
    pedido: "Pedido" = Relationship(back_populates="detalles")
    # No mantenemos Relationship con Producto porque es solo referencial

    def __repr__(self) -> str:
        return f"DetallePedido(id={self.id}, pedido_id={self.pedido_id}, cantidad={self.cantidad})"
