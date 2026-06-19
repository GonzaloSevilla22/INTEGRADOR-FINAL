from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Enum as SAEnum
from sqlmodel import Field, Relationship

from app.core.base import BaseModel
from app.models.producto_ingrediente import UnidadEnum

if TYPE_CHECKING:
    from app.models.producto_ingrediente import ProductoIngrediente


class Ingrediente(BaseModel, table=True):
    """
    Ingrediente global. Se asigna a Productos via ProductoIngrediente N:M.
    es_alergeno es un flag crítico para UX.
    """

    __tablename__ = "ingredientes"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100, unique=True, index=True, nullable=False)
    descripcion: Optional[str] = Field(default=None, nullable=True)
    es_alergeno: bool = Field(default=False, nullable=False)
    stock_actual: float = Field(default=0, ge=0, nullable=False)
    stock_minimo: float = Field(default=0, ge=0, nullable=False)
    costo_unitario: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=4)
    unidad_medida: UnidadEnum = Field(
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
    activo: bool = Field(default=True, nullable=False)

    # N:M hacia Productos
    productos_ingredientes: list["ProductoIngrediente"] = Relationship(
        back_populates="ingrediente"
    )
