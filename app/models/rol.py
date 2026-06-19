from typing import List, Optional

from sqlmodel import Field, Relationship

from app.core.base import BaseModel


class Rol(BaseModel, table=True):
    """
    Rol del sistema.
    PK: codigo (e.g., ADMIN, CLIENTE)
    """

    __tablename__ = "roles"

    codigo: str = Field(primary_key=True, max_length=50, nullable=False)
    nombre: str = Field(max_length=100, nullable=False, unique=True)
    descripcion: Optional[str] = Field(default=None, nullable=True)

    # Relación N:N con Usuario
    usuarios_roles: List["UsuarioRol"] = Relationship(back_populates="rol", cascade_delete=True)

    def __repr__(self) -> str:
        return f"Rol(codigo={self.codigo}, nombre={self.nombre})"
