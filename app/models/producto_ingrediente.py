from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.producto import Producto
    from app.models.ingrediente import Ingrediente


class UnidadEnum(str, Enum):
    """Unidades de medida para ingredientes."""
    GRAMOS = "gramos"
    LITROS = "litros"


class ProductoIngrediente(SQLModel, table=True):
    """
    Tabla intermedia N:M entre Producto e Ingrediente.
    Incluye cantidad y unidad de medida (gramos/litros).
    PK compuesta.
    
    Ejemplo: Pizza (id=1) + Queso (id=5) = 500 gramos.
    """

    __tablename__ = "productos_ingredientes"

    producto_id: int = Field(foreign_key="productos.id", primary_key=True, nullable=False)
    ingrediente_id: int = Field(foreign_key="ingredientes.id", primary_key=True, nullable=False)
    cantidad: float = Field(gt=0, nullable=False)  # 500, 250, 1.5, etc.
    unidad: UnidadEnum = Field(
        default=UnidadEnum.GRAMOS,
        sa_column=Column(
            SAEnum(
                UnidadEnum,
                values_callable=lambda enum_cls: [member.value for member in enum_cls],
                native_enum=False,
            ),
            nullable=False,
        ),
    )
    es_removible: bool = Field(default=False, nullable=False)
    es_opcional: bool = Field(default=False, nullable=False)

    producto: "Producto" = Relationship(back_populates="productos_ingredientes")
    ingrediente: "Ingrediente" = Relationship(back_populates="productos_ingredientes")
