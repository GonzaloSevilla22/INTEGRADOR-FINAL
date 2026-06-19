from typing import List, Optional

from sqlmodel import Field, Relationship

from app.core.base import BaseModel


class Usuario(BaseModel, table=True):
    """
    Usuario del sistema.
    Relaciones:
    - N:N con Rol (via UsuarioRol)
    - 1:N con DireccionEntrega
    - 1:N con Pedido
    Soft delete via activo=False (heredado de BaseModel con deleted_at)
    """

    __tablename__ = "usuarios"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100, nullable=False)
    apellido: str = Field(max_length=100, nullable=False)
    email: str = Field(max_length=255, nullable=False, unique=True, index=True)
    celular: Optional[str] = Field(default=None, max_length=20, nullable=True)
    password_hash: str = Field(max_length=255, nullable=False)
    activo: bool = Field(default=True, nullable=False)

    # Relaciones
    usuarios_roles: List["UsuarioRol"] = Relationship(
        back_populates="usuario",
        cascade_delete=True,
        sa_relationship_kwargs={"foreign_keys": "UsuarioRol.usuario_id"},
    )
    direcciones: List["DireccionEntrega"] = Relationship(back_populates="usuario", cascade_delete=True)
    pedidos: List["Pedido"] = Relationship(back_populates="usuario", cascade_delete=True)
    historiales: List["HistorialEstadoPedido"] = Relationship(back_populates="usuario")

    def __repr__(self) -> str:
        return f"Usuario(id={self.id}, email={self.email}, nombre={self.nombre} {self.apellido})"
