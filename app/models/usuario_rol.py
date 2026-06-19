from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.usuario import Usuario
    from app.models.rol import Rol


class UsuarioRol(SQLModel, table=True):
    """
    Tabla intermedia N:N entre Usuario y Rol.
    PK compuesta: usuario_id + rol_codigo
    """

    __tablename__ = "usuarios_roles"

    usuario_id: int = Field(foreign_key="usuarios.id", primary_key=True, nullable=False)
    rol_codigo: str = Field(foreign_key="roles.codigo", primary_key=True, max_length=50, nullable=False)
    asignado_por_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    expires_at: Optional[datetime] = Field(default=None)

    usuario: "Usuario" = Relationship(
        back_populates="usuarios_roles",
        sa_relationship_kwargs={"foreign_keys": "UsuarioRol.usuario_id"},
    )
    rol: "Rol" = Relationship(back_populates="usuarios_roles")
