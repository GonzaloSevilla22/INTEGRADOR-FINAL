from decimal import Decimal
from typing import List, Optional

from sqlmodel import JSON, Column, Field, Relationship

from app.core.base import BaseModel
from app.models.producto_categoria import ProductoCategoria
from app.models.producto_ingrediente import ProductoIngrediente


class Producto(BaseModel, table=True):
    """
    Producto del catálogo.
    Relaciones N:M: con Categoria (via ProductoCategoria) e Ingrediente (via ProductoIngrediente).
    SIN FK directo a Categoria.
    """

    __tablename__ = "productos"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=150, index=True, nullable=False)
    descripcion: Optional[str] = Field(default=None, nullable=True)
    precio_base: Decimal = Field(default=0, ge=0, max_digits=10, decimal_places=2, nullable=False)
    imagenes_url: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    tiempo_prep_min: Optional[int] = Field(default=None, ge=0, nullable=True)
    disponible: bool = Field(default=True, nullable=False)
    stock_cantidad: Optional[int] = Field(default=None, ge=0, nullable=True)
    unidad_venta_id: Optional[int] = Field(default=None, foreign_key="unidades_medida.id")
    usa_stock_manual: bool = Field(default=False, nullable=False)
    stock_manual: Optional[int] = Field(default=None, ge=0, nullable=True)
    costo_compra_manual: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=4,
        nullable=True,
    )
    activo: bool = Field(default=True, nullable=False)

    # N:M hacia Categorias
    productos_categorias: List[ProductoCategoria] = Relationship(
        back_populates="producto", cascade_delete=True
    )

    # N:M hacia Ingredientes
    productos_ingredientes: List[ProductoIngrediente] = Relationship(
        back_populates="producto", cascade_delete=True
    )
