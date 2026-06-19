from typing import List, Optional

from sqlmodel import Field, Relationship

from app.core.base import BaseModel
from app.models.producto_categoria import ProductoCategoria


class Categoria(BaseModel, table=True):
    """
    Categoría de productos con jerarquía (parent_id auto-referencia).
    Soporta N:M con Producto mediante ProductoCategoria.
    """

    __tablename__ = "categorias"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100, unique=True, index=True, nullable=False)
    descripcion: Optional[str] = Field(default=None, nullable=True)
    orden_display: int = Field(default=0, nullable=False)
    activo: bool = Field(default=True, nullable=False)
    imagen_url: Optional[str] = Field(default=None, max_length=500)

    parent_id: Optional[int] = Field(default=None, foreign_key="categorias.id", nullable=True)
    parent: Optional["Categoria"] = Relationship(
        back_populates="subcategorias",
        sa_relationship_kwargs={"remote_side": "Categoria.id"},
    )
    subcategorias: List["Categoria"] = Relationship(back_populates="parent")

    # N:M hacia Productos
    productos_categorias: List[ProductoCategoria] = Relationship(back_populates="categoria")

