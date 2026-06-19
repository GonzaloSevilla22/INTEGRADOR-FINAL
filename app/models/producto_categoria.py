from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.producto import Producto
    from app.models.categoria import Categoria


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class ProductoCategoria(SQLModel, table=True):
    """
    Tabla intermedia N:M entre Producto y Categoria.
    PK compuesta, es_principal flag, Relationships bidireccionales.
    """

    __tablename__ = "productos_categorias"

    producto_id: int = Field(foreign_key="productos.id", primary_key=True, nullable=False)
    categoria_id: int = Field(foreign_key="categorias.id", primary_key=True, nullable=False)
    es_principal: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(default_factory=now_utc, nullable=False)

    producto: "Producto" = Relationship(back_populates="productos_categorias")
    categoria: "Categoria" = Relationship(back_populates="productos_categorias")
